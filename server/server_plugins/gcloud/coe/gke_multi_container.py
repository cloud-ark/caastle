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
from server.common import exceptions
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
import server.server_plugins.app_base as app_base
import gke_app_base
from server.server_plugins.gcloud import gcloud_helper

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()

GCR = "us.gcr.io"


class GKEMultiContainer(gke_app_base.GKEAppBase):

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

    def _check_if_pod_or_more(self, app_id, app_info):
        only_pod = True

        kind_list = []
        
        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        df_dir = app_dir + "/" + app_folder_name
        app_yaml = app_info['app_yaml']

        stream = open(df_dir + "/" + app_yaml, "r")
        docs = yaml.load_all(stream)
        for doc in docs:
            for k,v in doc.items():
                if k == 'kind':
                    kind_list.append(v.strip())

        if 'Service' in kind_list or 'Deployment' in kind_list:
            only_pod = False
        return only_pod

    def _get_pod_name(self, app_info):
        app_yaml = common_functions.read_app_yaml(app_info)
        pod_name = app_yaml['metadata']['name']
        return pod_name

    def _get_container_port(self, app_info):
        container_port = ''

        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        app_yaml_dir = app_dir + "/" + app_folder_name
        app_yaml = app_info['app_yaml']

        app_yaml_file = app_yaml_dir + "/" + app_yaml

        fp = open(app_yaml_file, "r")
        for line in fp.readlines():
            if line.find("containerPort") >= 0:
                parts = line.split("containerPort:")
                container_port = parts[1].strip()
                break
        return container_port

    def _deploy_pod(self, app_id, app_info):
        df_file = self._get_kube_df_file(app_info)

        app_data = {}

        kubernetes_yaml = app_info['app_yaml']
        pod_name = self._get_pod_name(app_info)
        service_name = pod_name

        container_port = self._get_container_port(app_info)
        if not container_port:
            container_port = 80

        df_file = df_file + ("\n"
                             "WORKDIR /src \n"
                             "RUN kubectl create -f {kubernetes_yaml} \ \n"
                             " && kubectl expose pod {pod_name} --name {service_name} --type LoadBalancer --port 80 --target-port={container_port} --protocol TCP").format(
                                 kubernetes_yaml=kubernetes_yaml,
                                 pod_name=pod_name,
                                 service_name=service_name,
                                 container_port=container_port
                            )

        cont_name = app_info['app_name'] + "-deploy"

        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        df_dir = app_dir + "/" + app_folder_name
        df_name = df_dir + "/Dockerfile.deploy"
        fp = open(df_name, "w")
        fp.write(df_file)
        fp.close()

        err, output = self.docker_handler.build_container_image(
            cont_name,
            df_name,
            df_context=df_dir
        )

        if err:
            error_output = common_functions.filter_error_output(output)
            error_msg = ("Error encountered in building Dockerfile.deploy {e}").format(e=err)
            error_msg = error_msg + " " + error_output
            fmlogger.error(error_msg)
            raise exceptions.AppDeploymentFailure(error_msg)

        app_details = {}
        app_url, status = self._check_if_app_is_ready(app_id,
                                                      service_name,
                                                      app_details)

        app_data['status'] = status

        app_details['app_url'] = app_url
        app_details['pod_name'] = [pod_name]
        app_details['service_name'] = service_name
        app_details['app_folder_name'] = app_info['app_folder_name']
        app_details['env_name'] = app_info['env_name']
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

    def _deploy_service(self, app_id, app_info):
        pass

    def _deploy(self, app_id, app_info):

        only_pod_defined = self._check_if_pod_or_more(app_id, app_info)

        if only_pod_defined:
            self._deploy_pod(app_id, app_info)
        else:
            self._deploy_service(app_id, app_info)

    def deploy_application(self, app_id, app_info):
        fmlogger.debug("Deploying application %s" % app_info['app_name'])
        self._copy_creds(app_info)

        app_data = {}

        app_data['status'] = 'setting-up-kubernetes-config'
        app_db.App().update(app_id, app_data)
        try:
            self._setup_kube_config(app_info)
        except Exception as e:
            fmlogger.error("Exception encountered in obtaining kube config %s" % e)
            app_db.App().update(app_id, {'status': str(e)})

        # Resolve environment
        common_functions.resolve_environment_multicont(app_id, app_info)

        app_details = {}
        app_data = {}

        app_data['status'] = 'deploying'
        app_db.App().update(app_id, app_data)

        try:
            self._deploy(app_id, app_info)
            fmlogger.debug("Done deploying application %s" % app_info['app_name'])
        except exceptions.AppDeploymentFailure as e:
            fmlogger.error(str(e))
            app_data['status'] = 'deployment-failed ' + str(e) + " " + e.get_message()
            app_db.App().update(app_id, app_data)


    def redeploy_application(self, app_id, app_info):
        pass

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting application %s" % app_info['app_name'])

        app_obj = app_db.App().get(app_id)
        try:
            app_output_config = ast.literal_eval(app_obj.output_config)
            self._delete_service(app_info, app_output_config['service_name'])
            pod_name_list = app_output_config['pod_name']
            for pod in pod_name_list:
                self._delete_pod(app_info, pod)
        except Exception as e:
            fmlogger.error(e)

        app_db.App().delete(app_id)
        fmlogger.debug("Done deleting application %s" % app_info['app_name'])
    
    def get_logs(self, app_id, app_info):
        fmlogger.debug("Retrieving logs for application %s %s" % (app_id, app_info['app_name']))

        app_obj = app_db.App().get(app_id)
        output_config = ast.literal_eval(app_obj.output_config)

        pod_name_list = output_config['pod_name']
        log_list = []
        for pod in pod_name_list:      
            logs_path_list = self._retrieve_logs(app_info, pod)
            log_list.extend(logs_path_list)
        return log_list
