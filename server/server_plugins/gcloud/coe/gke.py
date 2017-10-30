import ast
import os
from os.path import expanduser
import shutil
import time

from kubernetes import client, config

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from server.common import common_functions
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
import server.server_plugins.coe_base as coe_base

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()

GCR = "us.gcr.io"


class GKEHandler(coe_base.COEBase):
    """GKE Handler."""
    
    def __init__(self):
        credentials = GoogleCredentials.get_application_default()
        self.gke_service = discovery.build('container', 'v1',
                                           credentials=credentials)
        self.compute_service = discovery.build('compute', 'v1',
                                               credentials=credentials,
                                               cache_discovery=False)
        self.docker_handler = docker_lib.DockerLib()

    def _get_cluster_name(self, env_id):
        resource_obj = res_db.Resource().get_resource_for_env(env_id, 'gke-cluster')
        cluster_name = resource_obj.cloud_resource_id
        return cluster_name

    def _get_cluster_node_ip(self, env_name, project, zone):
        pageToken = None
        list_of_node_objs = []
        list_of_ips = []

        resp = self.compute_service.instances().list(
            project=project, zone=zone, orderBy="creationTimestamp desc",
            pageToken=pageToken).execute()

        for res in resp['items']:
            if res['name'].lower().find(env_name) >= 0:
                list_of_node_objs.append(res)

        for res in list_of_node_objs:
            external_ip = res['networkInterfaces'][0]['accessConfigs'][0]['natIP']
            print(res)
            list_of_ips.append(external_ip.strip())
        return list_of_ips

    def _check_if_app_is_ready(self, app_id, app_info):
        fmlogger.debug("Checking if application is ready.")

        service_name = app_info['app_name']
        core_v1_api = client.CoreV1Api()

        app_ip = ''
        while not app_ip:
            api_response = core_v1_api.read_namespaced_service(
                name=service_name,
                namespace="default")

            if api_response.status.load_balancer.ingress is not None:
                app_ip = api_response.status.load_balancer.ingress[0].ip
                fmlogger.debug("Service IP:%s" % app_ip)
                if app_ip:
                    break
            else:
                time.sleep(5)

        app_url = "http://" + app_ip
        app_ready = common_functions.is_app_ready(app_url, app_id=app_id)

        if app_ready:
            return app_url, 'available'
        else:
            return app_url, 'failed-to-start'

    def _copy_creds(self, app_info):
        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        if not os.path.exists(df_dir + "/google-creds"):
            shutil.copytree(home_dir + "/.config/gcloud", df_dir + "/google-creds/gcloud")

    def _get_access_token(self, app_info):
        access_token = ''
        df = self.docker_handler.get_dockerfile_snippet("google")

        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        cont_name = app_info['app_name'] + "-get-access-token"

        df_dir = app_dir + "/" + app_folder_name
        fp = open(df_dir + "/Dockerfile.get-access-token", "w")
        fp.write(df)
        fp.close()

        err, output = self.docker_handler.build_container_image(
            cont_name,
            df_dir + "/Dockerfile.get-access-token",
            df_context=df_dir
        )
        
        err, output = self.docker_handler.run_container(cont_name)

        if err:
            error_msg = ("Error encountered in obtaining gcloud access token {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

        docker_image_id = output.strip()
        copy_creds_file = ("docker cp {docker_img}:/root/.config/gcloud/credentials {df_dir}/.").format(
            docker_img=docker_image_id,
            df_dir=df_dir
        )

        os.system(copy_creds_file)

        access_token = ''
        fp1 = open(df_dir + "/credentials")
        lines = fp1.readlines()
        for line in lines:
            if line.find("access_token") >= 0:
                line_contents = line.split(":")
                access_token = line_contents[1].strip().replace("\"", "").replace(",", "")
                fmlogger.debug("Access token:%s" % access_token)

        self.docker_handler.stop_container(docker_image_id)
        self.docker_handler.remove_container(docker_image_id)
        self.docker_handler.remove_container_image(cont_name)
        return access_token

    def _build_app_container(self, app_info, tag=''):
        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        env_obj = env_db.Environment().get(app_info['env_id'])
        env_details = ast.literal_eval(env_obj.env_definition)

        project = project = env_details['environment']['app_deployment']['project']
        app_name = app_info['app_name']
        cont_name = GCR + "/" + project + "/" + app_name
        fmlogger.debug("Container name that will be used in building:%s" % cont_name)

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile",
                                                                df_context=df_dir, tag=tag)
        return err, output, cont_name

    def _push_app_container(self, app_info, tagged_image):
        access_token = self._get_access_token(app_info)

        self.docker_handler.docker_login("oauth2accesstoken",
                                         access_token, "https://" + GCR)

        self.docker_handler.push_container(tagged_image)

    def _setup_kube_config(self, app_info):
        df = self.docker_handler.get_dockerfile_snippet("google")

        cluster_name = self._get_cluster_name(app_info['env_id'])
        kubectl = "curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"

        df = df + ("RUN /google-cloud-sdk/bin/gcloud container clusters get-credentials {cluster_name} \n"
                   "RUN {kubectl} \ \n"
                   " && chmod +x ./kubectl && mv ./kubectl /usr/local/bin/kubectl && kubectl get pods"
                   ).format(cluster_name=cluster_name,
                            kubectl=kubectl)

        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        cont_name = app_info['app_name'] + "-get-kubeconfig"

        df_dir = app_dir + "/" + app_folder_name
        df_name = df_dir + "/Dockerfile.get-kubeconfig"
        fp = open(df_name, "w")
        fp.write(df)
        fp.close()

        err, output = self.docker_handler.build_container_image(
            cont_name,
            df_name,
            df_context=df_dir
        )
        
        err, output = self.docker_handler.run_container(cont_name)

        if err:
            error_msg = ("Error encountered in setting up kube config {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

        docker_image_id = output.strip()
        if os.path.exists(home_dir + "/.kube/config"):
            kubeconfig_orig_ts = app_info['app_version']
            shutil.move(home_dir + "/.kube/config",
                        home_dir + "/.kube/config-" + kubeconfig_orig_ts)

        retrieve_creds_file = ("docker cp {docker_img}:/root/.kube/config {df_dir}/kube-config/").format(
            docker_img=docker_image_id,
            df_dir=df_dir
        )
        os.system(retrieve_creds_file)

        copy_creds_file = ("cp {df_dir}/kube-config/config {home_dir}/.kube/config").format(
            df_dir=df_dir,
            home_dir=home_dir
        )
        os.system(copy_creds_file)

        self.docker_handler.stop_container(docker_image_id)
        self.docker_handler.remove_container(docker_image_id)
        self.docker_handler.remove_container_image(cont_name)

        config.load_kube_config()

    def _create_deployment_object(self, app_info, tagged_image):
        deployment_name = app_info['app_name']
        container_port = int(app_info['app_port'])

        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=tagged_image,
            ports=[client.V1ContainerPort(container_port=container_port)])

        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
            spec=client.V1PodSpec(containers=[container]))

        # Create the specification of deployment
        spec = client.ExtensionsV1beta1DeploymentSpec(
            replicas=1,
            template=template)

        # Instantiate the deployment object
        deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec)
        return deployment

    def _create_deployment(self, deployment):
        extensions_v1beta1 = client.ExtensionsV1beta1Api()
        api_response = extensions_v1beta1.create_namespaced_deployment(
            body=deployment,
            namespace="default")
        fmlogger.debug("Deployment created. status='%s'" % str(api_response.status))

    def _create_service(self, app_info):
        deployment_name = app_info['app_name']
        container_port = int(app_info['app_port'])

        v1_object_meta = client.V1ObjectMeta()
        v1_object_meta.name = deployment_name

        v1_service_port = client.V1ServicePort()
        v1_service_port.port = 80
        v1_service_port.target_port = container_port

        v1_service_spec = client.V1ServiceSpec()
        v1_service_spec.ports = [v1_service_port]
        v1_service_spec.type = "LoadBalancer"
        v1_service_spec.selector = {"app": deployment_name}

        v1_service = client.V1Service()
        v1_service.spec = v1_service_spec
        v1_service.metadata = v1_object_meta

        core_v1 = client.CoreV1Api()
        api_response = core_v1.create_namespaced_service(
            namespace="default",
            body=v1_service)
        fmlogger.debug(api_response)

    def create_cluster(self, env_id, env_info):
        fmlogger.debug("Creating GKE cluster.")

        cluster_status = 'unavailable'

        env_obj = env_db.Environment().get(env_id)
        env_name = env_obj.name
        env_details = ast.literal_eval(env_obj.env_definition)

        env_output_config = ast.literal_eval(env_obj.output_config)
        env_version_stamp = env_output_config['env_version_stamp']

        cluster_name = env_name + "-" + env_version_stamp
        
        res_data = {}
        res_data['env_id'] = env_id
        res_data['cloud_resource_id'] = cluster_name
        res_data['type'] = 'gke-cluster'
        res_data['status'] = 'provisioning'
        res_id = res_db.Resource().insert(res_data)

        cluster_size = 1
        if 'cluster_size' in env_details['environment']['app_deployment']:
            cluster_size = env_details['environment']['app_deployment']['cluster_size']

        project = ""
        if 'project' in env_details['environment']['app_deployment']:
            project = env_details['environment']['app_deployment']['project']
        else:
            fmlogger("Project ID required. Not continuing with the request.")
            status = 'not-continuing-with-provisioning:missing parameter project id'
            res_data['status'] = status
            res_db.Resource().update(res_id, res_data)
            return status

        zone = ""
        if 'zone' in env_details['environment']['app_deployment']:
            zone = env_details['environment']['app_deployment']['zone']
        else:
            fmlogger("Zone required. Not continuing with the request.")
            status = 'not-continuing-with-provisioning:missing parameter zone'
            res_data['status'] = status
            res_db.Resource().update(res_id, res_data)
            return status

        resp = self.gke_service.projects().zones().clusters().create(
            projectId=project,
            zone=zone,
            body={"cluster": {"name": cluster_name,
                              "initialNodeCount": cluster_size,
                              "nodeConfig": {
                                  "oauthScopes": "https://www.googleapis.com/auth/devstorage.read_only"}}}
        ).execute()
    
        fmlogger.debug(resp)

        available = False
        while not available:
            resp = self.gke_service.projects().zones().clusters().get(
                projectId=project,
                zone=zone,
                clusterId=cluster_name).execute()
            status = resp['status']
            res_data['status'] = status
            res_db.Resource().update(res_id, res_data)
            if status.lower() == 'running' or status.lower() == 'available':
                available = True
                break
            else:
                time.sleep(3)

        instance_ip_list = self._get_cluster_node_ip(env_name,
                                                     project,
                                                     zone)

        cluster_status = 'available'
        env_output_config['cluster_ips'] = instance_ip_list
        env_data = {}
        env_data['output_config'] = str(env_output_config)
        env_db.Environment().update(env_id, env_data)
        res_data['status'] = cluster_status
        filtered_description = {}
        filtered_description['cluster_name'] = cluster_name
        filtered_description['cluster_ips'] = instance_ip_list
        filtered_description['project'] = project
        filtered_description['zone'] = zone
        res_data['filtered_description'] = str(filtered_description)
        res_db.Resource().update(res_id, res_data)
        fmlogger.debug("Done creating GKE cluster.")
        return cluster_status
        
    def delete_cluster(self, env_id, env_info, resource_obj):
        fmlogger.debug("Deleting GKE cluster")

        res_db.Resource().update(resource_obj.id, {'status': 'deleting'})

        filtered_description = ast.literal_eval(resource_obj.filtered_description)
        cluster_name = filtered_description['cluster_name']
        project = filtered_description['project']
        zone = filtered_description['zone']

        try:
            resp = self.gke_service.projects().zones().clusters().delete(
                projectId=project,
                zone=zone,
                clusterId=cluster_name
            ).execute()
            fmlogger.debug(resp)
        except Exception as e:
            fmlogger.error("Encountered exception when deleting cluster.")

        available = True
        while available:
            try:
                resp = self.gke_service.projects().zones().clusters().get(
                    projectId=project,
                    zone=zone,
                    clusterId=cluster_name).execute()
            except Exception as e:
                fmlogger.error("Exception encountered in retrieving cluster. Cluster does not exist. %s " % e)
                available = False
                break
            time.sleep(3)

        res_db.Resource().delete(resource_obj.id)
        fmlogger.debug("Done deleting GKE cluster.")

    def deploy_application(self, app_id, app_info):
        fmlogger.debug("Deploying application %s" % app_info['app_name'])
        self._copy_creds(app_info)
        
        if app_info['env_id']:
            common_functions.resolve_environment(app_id, app_info)

        app_data = {}
        app_data['status'] = 'building-application-container'
        app_db.App().update(app_id, app_data)
        tag = str(int(round(time.time() * 1000)))
        err, output, image_name = self._build_app_container(app_info, tag=tag)
        tagged_image = image_name + ":" + tag
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request. %s" % err)
            return

        app_data['status'] = 'pushing-app-cont-to-gcr-repository'
        app_db.App().update(app_id, app_data)
        try:
            self._push_app_container(app_info, tagged_image)
        except Exception as e:
            fmlogger.error("Exception encountered in pushing app container to gcr %s" % e)
            app_data['status'] = 'error-in-application-push-to-gcr'
            app_db.App().update(app_id, app_data)
            return

        app_data['status'] = 'setting-up-kubernetes-config'
        app_db.App().update(app_id, app_data)
        self._setup_kube_config(app_info)

        app_data['status'] = 'creating-deployment-object'
        app_db.App().update(app_id, app_data)
        deployment_obj = self._create_deployment_object(app_info,
                                                        tagged_image)

        app_data['status'] = 'creating-kubernetes-deployment'
        app_db.App().update(app_id, app_data)
        self._create_deployment(deployment_obj)

        app_data['status'] = 'creating-kubernetes-service'
        app_db.App().update(app_id, app_data)
        self._create_service(app_info)

        app_data['status'] = 'creating-kubernetes-service'
        app_db.App().update(app_id, app_data)

        app_data['status'] = 'waiting-for-app-to-get-ready'
        app_db.App().update(app_id, app_data)

        app_url, status = self._check_if_app_is_ready(app_id,
                                                      app_info)

        fmlogger.debug('Application URL:%s' % app_url)

        app_data['status'] = status
        app_details = {}
        app_details['app_url'] = app_url
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        fmlogger.debug("Done deploying application %s" % app_info['app_name'])

    def redeploy_application(self, app_id, app_info):
        pass

    def delete_application(self, app_id, app_info):
        pass
