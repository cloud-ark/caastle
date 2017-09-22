import ast
import boto3
import os
import subprocess
import time

from common import constants
from common import fm_logger
from common import docker_lib
from common import common_functions
from dbmodule import db_handler

fmlogger = fm_logger.Logging()

dbhandler = db_handler.DBHandler()

tagged_images_file = 'tagged_images.txt'

class LocalHandler(object):

    def __init__(self):
        self.docker_handler = docker_lib.DockerLib()

    def _build_app_container(self, app_info):
        app_dir = app_info['app_location']
        app_name = app_info['app_name']
        app_version = app_info['app_version']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        cont_name = app_name + "-" + app_version
        fmlogger.debug("Container name that will be used in building:%s" % cont_name)

        tag = str(int(round(time.time() * 1000)))

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile", 
                                                                df_context=df_dir, tag=tag)

        tagged_image = cont_name + ":" + tag
        common_functions.save_image_tag(tagged_image, app_info, file_name=tagged_images_file)

        return err, output, tagged_image

    def _parse_app_port(self, cont_id):
        inspect_cmd = ("docker inspect {cont_id}").format(cont_id=cont_id)
        port = ''
        try:
            out = subprocess.Popen(inspect_cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True).communicate()[0]
            all_lines = out.split("\n")
            for line in all_lines:
                if line.find("HostPort") >= 0:
                    parts = line.split(":")
                    port = parts[1].replace('"',"").rstrip().lstrip()
                    if port and port != 'null':
                        break
        except Exception as e:
            fmlogger.error(e)

        return port

    def _deploy_app_container(self, cont_name, app_info):
        app_url = ''
        app_status = ''
        err, cont_id = self.docker_handler.run_container(cont_name)

        if err:
            fmlogger.debug("Encountered error in deploying application container:%s. Returning." % cont_name)
            return app_url

        common_functions.save_container_id(cont_id, app_info)

        app_ip_addr = 'localhost'
        app_port = self._parse_app_port(cont_id)

        app_url = ("http://{app_ip_addr}:{app_port}").format(app_ip_addr=app_ip_addr,
                                                             app_port=app_port)
        fmlogger.debug("App URL: %s" % app_url)
        if common_functions.is_app_ready(app_url):
            fmlogger.debug("Application is ready.")
            app_status = constants.APP_DEPLOYMENT_COMPLETE
        else:
            fmlogger.debug("Application could not start properly.")
            app_status = constants.APP_DEPLOYMENT_TIMEOUT
        return app_url, app_status

    def deploy_application(self, app_id, app_info):
        fmlogger.debug("Deploying application %s %s" % (app_id, app_info['app_name']))
        if 'env_id' in app_info:
            common_functions.resolve_environment(app_id, app_info)
        dbhandler.update_app(app_id, status=constants.BUILDING_APP)
        err, output, cont_name = self._build_app_container(app_info)
        if err:
            fmlogger.debug("Encountered error in building application container:%s. Returning." % cont_name)
            return
        
        dbhandler.update_app(app_id, status=constants.DEPLOYING_APP)
        app_url, app_status = self._deploy_app_container(cont_name, app_info)
        
        if app_url:
            dbhandler.update_app(app_id, status=app_status, output_config=app_url)
        else:
            dbhandler.update_app(app_id, status=constants.DEPLOYMENT_ERROR)
        fmlogger.debug("Done deploying application")

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting application %s %s" % (app_id, app_info['app_name']))
        cont_image_name = app_info['app_name'] + '-' + app_info['app_version']
        dbhandler.update_app(app_id, status=constants.DELETING_APP)
        cont_id_list = common_functions.read_container_id(app_info)
        if cont_id_list:
            for cont_id in cont_id_list:
                err, output = self.docker_handler.stop_container(cont_id)
                if err:
                    fmlogger.debug("Encountered error in stopping container %s." % cont_id)
                self.docker_handler.remove_container(cont_id)

        tagged_image_list = common_functions.read_image_tag(app_info, file_name=tagged_images_file)
        if tagged_image_list:
            for tagged_image in tagged_image_list:
                self.docker_handler.remove_container_image(tagged_image)

        self.docker_handler.remove_container_image(cont_image_name)
        dbhandler.delete_app(app_id)
        fmlogger.debug("Done deleting application")