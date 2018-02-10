import ast
import os
from os.path import expanduser
import shutil
import time
import yaml

from kubernetes import client, config

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from server.common import constants
from server.common import common_functions
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
import server.server_plugins.app_base as app_base
from server.server_plugins.gcloud import gcloud_helper

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

SERVICE_ACCOUNT_FILE = APP_AND_ENV_STORE_PATH + "gcp-service-account-key.json"

fmlogger = fm_logger.Logging()

GCR = "us.gcr.io"


class GKEAppBase(app_base.AppBase):
    """GKE App Base."""

    gcloudhelper = gcloud_helper.GCloudHelper()
    
    def __init__(self):
        credentials = GoogleCredentials.get_application_default()
        self.gke_service = discovery.build('container', 'v1',
                                           credentials=credentials)
        self.compute_service = discovery.build('compute', 'v1',
                                               credentials=credentials,
                                               cache_discovery=False)
        self.docker_handler = docker_lib.DockerLib()

        self.app_yaml_def = ''

    def _get_cluster_name(self, env_id):
        resource_obj = res_db.Resource().get_resource_for_env_by_type(env_id, 'gke-cluster')
        cluster_name = resource_obj.cloud_resource_id
        return cluster_name

    def _copy_creds(self, app_info):
        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        if not os.path.exists(df_dir + "/google-creds"):
            shutil.copytree(home_dir + "/.config/gcloud", df_dir + "/google-creds/gcloud")

    def _get_access_token(self, app_info):
        access_token = ''
        df = self.docker_handler.get_dockerfile_snippet("google_for_token")

        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        cont_name = app_info['app_name'] + "-get-access-token"

        df_dir = app_dir + "/" + app_folder_name

        access_token = GKEAppBase.gcloudhelper.get_access_token(df_dir, cont_name)
        
        return access_token

    def _get_ports(self, app_info):
        port_list = common_functions.get_app_port(app_info)
        container_port = int(port_list[0])
        host_port = int(port_list[1])
        return container_port, host_port

    def _get_kube_df_file(self, app_info):
        df = self.docker_handler.get_dockerfile_snippet("gke")

        cluster_name = self._get_cluster_name(app_info['env_id'])

        user_account, project_name, zone_name = GKEAppBase.gcloudhelper.get_deployment_details(app_info['env_id'])
        df = df + ("RUN /google-cloud-sdk/bin/gcloud config set account {account} \ \n"
                   " && /google-cloud-sdk/bin/gcloud config set project {project} \n"
                   "RUN /google-cloud-sdk/bin/gcloud container clusters get-credentials {cluster_name} --zone {zone} \ \n"
                   " && kubectl get pods "
                   ).format(account=user_account,
                            project=project_name,
                            cluster_name=cluster_name,
                            zone=zone_name)

        return df

    def _setup_kube_config(self, app_info):
        df = self._get_kube_df_file(app_info)
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

        if err:
            error_msg = ("Error encountered in setting up kube config {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

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
        kube_config_path = ("{df_dir}/kube-config/").format(df_dir=df_dir)
        if not os.path.exists(kube_config_path):
            os.system("mkdir " + kube_config_path)
        fmlogger.debug(retrieve_creds_file)
        os.system(retrieve_creds_file)

        copy_creds_file = ("cp {df_dir}/kube-config/config {home_dir}/.kube/config").format(
            df_dir=df_dir,
            home_dir=home_dir
        )
        home_kube_config_path = ("{home_dir}/.kube/").format(home_dir=home_dir)
        if not os.path.exists(home_kube_config_path):
            os.system("mkdir " + home_kube_config_path)
        fmlogger.debug(copy_creds_file)
        os.system(copy_creds_file)

        self.docker_handler.stop_container(docker_image_id)
        self.docker_handler.remove_container(docker_image_id)
        self.docker_handler.remove_container_image(cont_name)

        config.load_kube_config()

    def _check_if_app_is_ready(self, app_id, service_name, app_details):
        fmlogger.debug("Checking if application is ready.")

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

        app_details['app_url'] = app_url
        app_db.App().update(app_id, {'output_config': str(app_details)})

        app_ready = common_functions.is_app_ready(app_url, app_id=app_id)

        if app_ready:
            return app_url, 'available'
        else:
            return app_url, 'failed-to-start'

    def _delete_service(self, app_info, service_name):
        fmlogger.debug("Deleting GKE app service")
        core_v1 = client.CoreV1Api()
        try:
            api_response = core_v1.delete_namespaced_service(
                name=service_name,
                namespace="default")
            fmlogger.debug("Delete service response:%s" % api_response)
        except Exception as e:
            fmlogger.error(e)
            raise e

    def _delete_deployment(self, app_info, deployment_name):
        fmlogger.debug("Deleting GKE app deployment")
        extensions_v1beta1 = client.ExtensionsV1beta1Api()
        delete_options = client.V1DeleteOptions()
        delete_options.grace_period_seconds = 0
        delete_options.propagation_policy = 'Foreground'
        try:
            api_response = extensions_v1beta1.delete_namespaced_deployment(
                name=deployment_name,
                body=delete_options,
                grace_period_seconds=0,
                namespace="default")
            fmlogger.debug("Delete deployment response:%s" % api_response)
        except Exception as e:
            fmlogger.error(e)
            raise e
        
    def _delete_pod(self, app_info, pod_name):
        fmlogger.debug("Deleting GKE app deployment")
        core_v1 = client.CoreV1Api()
        delete_options = client.V1DeleteOptions()
        delete_options.grace_period_seconds = 0
        delete_options.propagation_policy = 'Foreground'
        try:
            api_response = core_v1.delete_namespaced_pod(
                name=pod_name,
                body=delete_options,
                grace_period_seconds=0,
                namespace="default")
            fmlogger.debug("Delete pod response:%s" % api_response)
        except Exception as e:
            fmlogger.error(e)
            raise e

    def _get_container_names(self, app_name):
        pod_name = ''
        container_name_set = set()
        app_obj = app_db.App().get_by_name(app_name)
        app_yaml = ast.literal_eval(app_obj.app_yaml_contents)

        if 'kind' in app_yaml and app_yaml['kind'] == 'Pod':
            pod_name = app_yaml['metadata']['name']

            # There could be multiple documents -- eventually
            #for doc in app_yaml:
            container_name_set = common_functions.get_cont_names(app_yaml,
                                                                 container_name_set)
        return container_name_set

    def _retrieve_runtime_logs(self, app_info, pod_name, app_name):
        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        df_dir = app_dir + "/" + app_folder_name

        logs_path = []

        df = self._get_kube_df_file(app_info)

        get_logs = "get-runtimelogs.sh"
        get_logs_wrapper = df_dir + "/" + get_logs

        container_names = self._get_container_names(app_name)

        logs_command_list = []
        if len(container_names) > 0:
            for cont_name in container_names:
                echo_command = ('echo "-- Logs for container {cont_name} --" \n').format(cont_name=cont_name)
                logs_command = ("kubectl logs {pod_name} {cont_name} \n").format(pod_name=pod_name,
                                                                              cont_name=cont_name)
                logs_command_list.append(echo_command)
                logs_command_list.append(logs_command)
        else:
            logs_command = ("kubectl get pods | grep {pod_name} | awk '{{print $1}}' | xargs kubectl logs \n").format(
                            pod_name=pod_name)
            logs_command_list.append(logs_command)

        #if not os.path.exists(get_logs_wrapper):
        fp = open(get_logs_wrapper, "w")
        file_content = ("#!/bin/bash \n")
        fp.write(file_content)

        for cmd in logs_command_list:
            fp.write(cmd)

        fp.flush()
        fp.close()
        change_perm_command = ("chmod +x {get_logs_wrapper}").format(get_logs_wrapper=get_logs_wrapper)
        os.system(change_perm_command)

        logs_wrapper_cmd = ("\n"
                            "CMD [\"sh\", \"/src/get-runtimelogs.sh\"] ")

        df = df + logs_wrapper_cmd

        log_cont_name = app_info['app_name'] + "-get-runtimelogs"

        df_name = df_dir + "/Dockerfile.get-runtimelogs"
        fp = open(df_name, "w")
        fp.write(df)
        fp.close()

        err, output = self.docker_handler.build_container_image(
            log_cont_name,
            df_name,
            df_context=df_dir
        )

        if err:
            error_msg = ("Error {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)
        else:
            err1, output1 = self.docker_handler.run_container(log_cont_name)
            if not err1:
                logs_cont_id = output1.strip()
                logs_output = self.docker_handler.get_logs(logs_cont_id)

                logs_dir = ("{app_dir}/logs").format(app_dir=app_dir)

                runtime_log = app_info['app_name'] + constants.RUNTIME_LOG
                runtime_log_path = logs_dir + "/" + runtime_log

                fp1 = open(runtime_log_path, "w")
                fp1.writelines(logs_output)
                fp1.flush()
                fp1.close()

                self.docker_handler.stop_container(logs_cont_id)
                self.docker_handler.remove_container(logs_cont_id)
                self.docker_handler.remove_container_image(log_cont_name)

                logs_path.append(runtime_log_path)
        return logs_path

    def _retrieve_deploy_logs(self, app_info, app_name):
        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        df_dir = app_dir + "/" + app_folder_name

        logs_path = []
        try:
            self._setup_kube_config(app_info)
        except Exception as e:
            fmlogger.error("Exception encountered in obtaining kube config %s" % e)
            app_db.App().update(app_id, {'status': str(e)})

        df = self._get_kube_df_file(app_info)

        get_logs = "get-deploytimelogs.sh"
        get_logs_wrapper = df_dir + "/" + get_logs

        #if not os.path.exists(get_logs_wrapper):
        fp = open(get_logs_wrapper, "w")
        file_content = ("#!/bin/bash \n"
                        "kubectl get pods | grep {app_name} | awk '{{print $1}}' | xargs kubectl describe pods").format(
                         app_name=app_name)
        fp.write(file_content)
        fp.flush()
        fp.close()
        change_perm_command = ("chmod +x {get_logs_wrapper}").format(get_logs_wrapper=get_logs_wrapper)
        os.system(change_perm_command)

        logs_wrapper_cmd = ("\n"
                            "CMD [\"sh\", \"/src/get-deploytimelogs.sh\"] ")

        df = df + logs_wrapper_cmd

        log_cont_name = app_info['app_name'] + "-get-deploytimelogs"

        df_name = df_dir + "/Dockerfile.get-deploytimelogs"
        fp = open(df_name, "w")
        fp.write(df)
        fp.close()

        err, output = self.docker_handler.build_container_image(
            log_cont_name,
            df_name,
            df_context=df_dir
        )

        if err:
            error_msg = ("Error {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)
        else:
            err1, output1 = self.docker_handler.run_container(log_cont_name)
            if not err1:
                logs_cont_id = output1.strip()
                logs_output = self.docker_handler.get_logs(logs_cont_id)

                logs_dir = ("{app_dir}/logs").format(app_dir=app_dir)
                logs_dir_command = ("mkdir {logs_dir}").format(logs_dir=logs_dir)
                os.system(logs_dir_command)

                deploy_log = app_info['app_name'] + constants.DEPLOY_LOG
                deploy_log_path = logs_dir + "/" + deploy_log

                fp1 = open(deploy_log_path, "w")
                fp1.writelines(logs_output)
                fp1.flush()
                fp1.close()

                self.docker_handler.stop_container(logs_cont_id)
                self.docker_handler.remove_container(logs_cont_id)
                self.docker_handler.remove_container_image(log_cont_name)

                logs_path.append(deploy_log_path)
        return logs_path

    def _retrieve_logs(self, app_info, pod_name, app_name=''):
        all_logs = []
        deploy_logs = self._retrieve_deploy_logs(app_info, pod_name)
        runtime_logs = self._retrieve_runtime_logs(app_info, pod_name, app_name)
        all_logs.extend(deploy_logs)
        all_logs.extend(runtime_logs)
        return all_logs

    def deploy_application(self, app_id, app_info):
        pass
    
    def redeploy_application(self, app_id, app_info):
        pass
    
    def delete_application(self, app_id, app_info):
        pass
    
    def get_logs(self, app_id, app_info):
        pass