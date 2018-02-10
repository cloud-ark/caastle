import ast
import os
from os.path import expanduser
import shutil
import time

from kubernetes import client, config

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from google.oauth2 import service_account

from server.common import constants
from server.common import common_functions
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
import server.server_plugins.app_base as app_base
import gke_app_base
from server.server_plugins.gcloud import gcloud_helper

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

SERVICE_ACCOUNT_FILE = APP_AND_ENV_STORE_PATH + "gcp-service-account-key.json"

fmlogger = fm_logger.Logging()

GCR = "us.gcr.io"


class GKESingleContainer(gke_app_base.GKEAppBase):

    gcloudhelper = gcloud_helper.GCloudHelper()
    
    def __init__(self):
        #credentials = GoogleCredentials.get_application_default()
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        self.gke_service = discovery.build('container', 'v1',
                                           credentials=credentials)
        self.compute_service = discovery.build('compute', 'v1',
                                               credentials=credentials,
                                               cache_discovery=False)
        self.docker_handler = docker_lib.DockerLib()

        self.app_yaml_def = ''

    def _create_deployment_object(self, app_info, tagged_image, env_vars_dict, alternate_api=False):
        deployment_name = app_info['app_name']

        container_port, host_port = self._get_ports(app_info)

        env_list = []
        for key, value in env_vars_dict.iteritems():
            v1_envvar = client.V1EnvVar(name=key, value=value)
            env_list.append(v1_envvar)

        # Configure Pod template container
        container = client.V1Container(
            name=deployment_name,
            image=tagged_image,
            ports=[client.V1ContainerPort(container_port=container_port)],
            env=env_list)

        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
            spec=client.V1PodSpec(containers=[container]))

        deployment = ''
        if not alternate_api:
            # Create the specification of deployment
            spec = client.AppsV1beta1DeploymentSpec(
                replicas=1,
                template=template)

            # Instantiate the deployment object
            deployment = client.AppsV1beta1Deployment(
                api_version="apps/v1beta1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=deployment_name),
                spec=spec)
        else:
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

    def _create_deployment(self, deployment, alternate_api=False):
        if not alternate_api:
            apps_v1beta1 = client.AppsV1beta1Api()
            api_response = apps_v1beta1.create_namespaced_deployment(
                body=deployment,
                namespace="default")
            fmlogger.debug("Deployment created. status='%s'" % str(api_response.status))
        else:
            extensions_v1beta1 = client.ExtensionsV1beta1Api()
            api_response = extensions_v1beta1.create_namespaced_deployment(
                body=deployment,
                namespace="default")
            fmlogger.debug("Deployment created. status='%s'" % str(api_response.status))

    def _create_service(self, app_info):
        deployment_name = app_info['app_name']

        container_port, host_port = self._get_ports(app_info)

        v1_object_meta = client.V1ObjectMeta()
        v1_object_meta.name = deployment_name

        v1_service_port = client.V1ServicePort(port=host_port,
                                               target_port=container_port)

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

    def deploy_application(self, app_id, app_info):
        fmlogger.debug("Deploying application %s" % app_info['app_name'])
        self._copy_creds(app_info)

        env_vars = common_functions.resolve_environment(app_id, app_info)

        app_details = {}
        app_data = {}

        app_data['status'] = 'setting-up-kubernetes-config'
        app_db.App().update(app_id, app_data)
        try:
            self._setup_kube_config(app_info)
        except Exception as e:
            fmlogger.error("Exception encountered in obtaining kube config %s" % e)
            app_db.App().update(app_id, {'status': str(e)})

        app_data['status'] = 'creating-deployment-object'
        app_db.App().update(app_id, app_data)

        tagged_image = common_functions.get_image_uri(app_info)

        deployment_obj = self._create_deployment_object(app_info,
                                                        tagged_image,
                                                        env_vars)

        app_data['status'] = 'creating-kubernetes-deployment'
        app_db.App().update(app_id, app_data)

        try:
            self._create_deployment(deployment_obj)
        except Exception as e:
            fmlogger.error(e)
            deployment_obj = self._create_deployment_object(app_info,
                                                            tagged_image,
                                                            env_vars,
                                                            alternate_api=True)
            try:
                self._create_deployment(deployment_obj, alternate_api=True)
            except Exception as e:
                fmlogger.error(e)
                app_data['status'] = 'deployment-error ' + str(e)
                app_db.App().update(app_id, app_data)
                return

        app_data['status'] = 'creating-kubernetes-service'
        app_db.App().update(app_id, app_data)
        try:
            self._create_service(app_info)
        except Exception as e:
            fmlogger.error(e)

        container_port, host_port = self._get_ports(app_info)
        app_details['cluster_name'] = self._get_cluster_name(app_info['env_id'])
        app_details['image_name'] = [tagged_image]
        app_details['memory'] = common_functions.get_app_memory(app_info)
        app_details['app_folder_name'] = app_info['app_folder_name']
        app_details['env_name'] = app_info['env_name']
        app_details['container_port'] = container_port
        app_details['host_port'] = host_port

        app_data['output_config'] = str(app_details)
        app_data['status'] = 'creating-kubernetes-service'
        app_db.App().update(app_id, app_data)

        app_data['status'] = 'waiting-for-app-to-get-ready'
        app_db.App().update(app_id, app_data)

        app_url, status = self._check_if_app_is_ready(app_id,
                                                      app_info['app_name'],
                                                      app_details)

        fmlogger.debug('Application URL:%s' % app_url)

        app_data['status'] = status

        app_details['app_url'] = app_url
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        fmlogger.debug("Done deploying application %s" % app_info['app_name'])

    def redeploy_application(self, app_id, app_info):
        pass

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting application %s" % app_info['app_name'])

        app_obj = app_db.App().get(app_id)
        try:
            app_output_config = ast.literal_eval(app_obj.output_config)
            self._delete_service(app_info, app_info['app_name'])
            self._delete_deployment(app_info, app_info['app_name'])

            # TODO(devdatta) The gcloud sdk is encountering a failure when trying
            # to delete the GCR image. So for the time being commenting out below
            # call. Send a response to the user asking the user to manually delete
            # the image from Google cloud console.
            # self._delete_app_image_gcr(tagged_image, app_info)

            #tagged_image = app_output_config['tagged_image']
            #self._delete_app_image_local(tagged_image)
        except Exception as e:
            fmlogger.error(e)

        app_db.App().delete(app_id)
        fmlogger.debug("Done deleting application %s" % app_info['app_name'])

    def get_logs(self, app_id, app_info):
        fmlogger.debug("Retrieving logs for application %s %s" % (app_id, app_info['app_name']))
        logs_path_list = self._retrieve_logs(app_info, app_info['app_name'], app_name=app_info['app_name'])
        return logs_path_list
