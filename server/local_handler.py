import ast
import boto3
import os
import time
import subprocess

from common import constants
from common import fm_logger
from dbmodule import db_handler
from common import docker_lib
from common import common_functions

fmlogger = fm_logger.Logging()

dbhandler = db_handler.DBHandler()

class LocalHandler(object):

    def __init__(self):
        self.docker_handler = docker_lib.DockerLib()
        
    def _save_container_id(self, cont_id, app_info):
        app_dir = app_info['app_location']
        fp = open(app_dir + "/container_id.txt", "w")
        fp.write(cont_id)
        fp.flush()
        fp.close()

    def _read_container_id(self, app_info):
        cont_id = ''
        try:
            app_dir = app_info['app_location']
            fp = open(app_dir + "/container_id.txt", "r")
            cont_id = fp.readline().rstrip().lstrip()
        except Exception as e:
            fmlogger.debug("Error encountered in reading container_id: %s" % e)
        return cont_id

    def _build_app_container(self, app_info):
        app_dir = app_info['app_location']
        app_name = app_info['app_name']
        app_version = app_info['app_version']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        cont_name = app_name + "-" + app_version
        fmlogger.debug("Container name that will be used in building:%s" % cont_name)

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile", 
                                                                df_context=df_dir)
        return err, output, cont_name

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
        err, output = self.docker_handler.run_container(cont_name)

        if err:
            fmlogger.debug("Encountered error in deploying application container:%s. Returning." % cont_name)
            return app_url
        
        cont_id = output
        self._save_container_id(cont_id, app_info)

        app_ip_addr = 'localhost'
        app_port = self._parse_app_port(cont_id)

        app_url = ("{app_ip_addr}:{app_port}").format(app_ip_addr=app_ip_addr,
                                                      app_port=app_port)

        fmlogger.debug("App URL: %s" % app_url)
        return app_url

    def deploy_application(self, app_id, app_info):
        fmlogger.debug("Deploying application %s %s" % (app_id, app_info['app_name']))
        if app_info['env_id']:
            common_functions.resolve_environment(app_id, app_info)
        dbhandler.update_app(app_id, status=constants.BUILDING_APP)
        err, output, cont_name = self._build_app_container(app_info)
        if err:
            fmlogger.debug("Encountered error in building application container:%s. Returning." % cont_name)
            return
        
        dbhandler.update_app(app_id, status=constants.DEPLOYING_APP)
        app_url = self._deploy_app_container(cont_name, app_info)
        
        if app_url:
            dbhandler.update_app(app_id, status=constants.APP_DEPLOYMENT_COMPLETE, output_config=app_url)
        else:
            dbhandler.update_app(app_id, status=constants.DEPLOYMENT_ERROR)
        fmlogger.debug("Done deploying application")

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting application %s %s" % (app_id, app_info['app_name']))
        dbhandler.update_app(app_id, status=constants.DELETING_APP)
        cont_id = self._read_container_id(app_info)
        if cont_id:
            err, output = self.docker_handler.stop_container(cont_id)
            if err:
                fmlogger.debug("Encountered error in stopping container %s. Returning." % cont_id)
            self.docker_handler.remove_container(cont_id)
        dbhandler.delete_app(app_id)
        fmlogger.debug("Done deleting application")