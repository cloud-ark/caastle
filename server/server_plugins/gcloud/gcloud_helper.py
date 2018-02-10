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

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

GOOGLE_CREDS_FILE = APP_AND_ENV_STORE_PATH + "google-creds-cloudark"

fmlogger = fm_logger.Logging()

GCR = "us.gcr.io"


class GCloudHelper(object):
    
    def __init__(self):
        self.docker_handler = docker_lib.DockerLib()
    
    def get_access_token(self, df_dir, df, cont_name):
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

    def get_deployment_details(self, env_id):
        project = ''
        zone = ''
        account = ''

        if 'app_deployment' in env_details['environment']:
            project = env_details['environment']['app_deployment']['project']
            zone = env_details['environment']['app_deployment']['zone']
        else:
            project = env_details['environment']['resources']['gcloud'][0]['resource']['project']
            zone = env_details['environment']['resources']['gcloud'][0]['resource']['zone']

        fp = open(GOOGLE_CREDS_FILE, "r")
        lines = fp.readlines()
        for line in lines:
            parts = line.split(":")
            if parts[0].strip() == 'zone':
                zone = parts[1].strip()
            if parts[0].strip() == 'account':
                account = parts[1].strip()

        return account, project, zone

    def get_deployment_details_bak(self, env_id):
        env_obj = env_db.Environment().get(env_id)
        env_details = ast.literal_eval(env_obj.env_definition)
        project = ''
        zone = ''
        if 'app_deployment' in env_details['environment']:
            project = env_details['environment']['app_deployment']['project']
            zone = env_details['environment']['app_deployment']['zone']
        else:
            project = env_details['environment']['resources']['gcloud'][0]['resource']['project']
            zone = env_details['environment']['resources']['gcloud'][0]['resource']['zone']

        user_account = ''
        if not os.path.exists(home_dir + "/.config/gcloud/configurations/config_default"):
            fmlogger.error("gcloud sdk installation not proper. Did not find ~/.config/gcloud/configurations/config_default file")
            raise Exception()
        else:
            fp = open(home_dir + "/.config/gcloud/configurations/config_default", "r")
            lines = fp.readlines()
            for line in lines:
                if line.find("account") >= 0:
                    parts = line.split("=")
                    user_account = parts[1].strip()
                    break
        return user_account, project, zone

    def run_command(self, env_id, env_name, resource_obj, base_command, command, base_image):

        command_output = ''
        env_obj = env_db.Environment().get(env_id)
        df_dir = env_obj.location

        if not os.path.exists(df_dir):
            mkdir_command = ("mkdir {df_dir}").format(df_dir=df_dir)
            os.system(mkdir_command)

        if not os.path.exists(df_dir + "/google-creds"):
            shutil.copytree(home_dir + "/.config/gcloud", df_dir + "/google-creds/gcloud")

        user_account, project_name, zone_name = self.get_deployment_details(env_id)

        df = self.docker_handler.get_dockerfile_snippet(base_image)
        df = df + ("RUN /google-cloud-sdk/bin/gcloud config set account {account} \ \n"
                   " && /google-cloud-sdk/bin/gcloud config set project {project} \n"
                   "{base_command}"
                   "WORKDIR /src \n"
                   "CMD [\"sh\", \"/src/run_command.sh\"] "
                   ).format(account=user_account,
                            project=project_name,
                            base_command=base_command
                            )
        df_name = df_dir + "/Dockerfile.run_command"
        fp = open(df_name, "w")
        fp.write(df)
        fp.close()

        fp1 = open(df_dir + "/run_command.sh", "w")
        fp1.write("#!/bin/bash \n")
        fp1.write(command)
        fp1.close()

        time1 = int(round(time.time() * 1000))
        resource_name = resource_obj.cloud_resource_id
        cont_name = resource_name + "_run_command"

        err, output = self.docker_handler.build_container_image(
            cont_name,
            df_name,
            df_context=df_dir
        )

        time2 = int(round(time.time() * 1000))

        if err:
            error_msg = ("Error encountered in running command {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

        err, output = self.docker_handler.run_container(cont_name)

        time3 = int(round(time.time() * 1000))

        if err:
            error_msg = ("Error encountered in running command {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

        cont_id = output.strip()

        err, command_output = self.docker_handler.get_logs(cont_id)
        time4 = int(round(time.time() * 1000))

        #self.docker_handler.stop_container(cont_id)
        self.docker_handler.remove_container(cont_id)
        time5 = int(round(time.time() * 1000))

        self.docker_handler.remove_container_image(cont_name)
        time6 = int(round(time.time() * 1000))

        build_time = time2 - time1
        run_time = time3 - time2
        logs_time = time4 - time3
        remove_cont_time = time5 - time4
        remove_image_time = time6 - time5

        timings1 = ("Build time:{build_time}, Run time:{run_time}, logs time:{logs_time}").format(
            build_time=build_time, run_time=run_time, logs_time=logs_time
        )

        timings2 = (" Cont remove time:{remove_cont_time}, Cont image remove time:{remove_image_time}").format(
            remove_cont_time=remove_cont_time, remove_image_time=remove_image_time
        )

        fmlogger.error("Build time: %s %s" % (timings1, timings2))

        return command_output

    def resource_type_for_command(self, command):
        resource_type_for_command = {}
        resource_type_for_command["gcloud sql"] = 'cloudsql'
        resource_type_for_command["kubectl"] = 'gke'

        type = ''
        for key, value in resource_type_for_command.iteritems():
            if command.find(key) >= 0:
                type = value

        return type
