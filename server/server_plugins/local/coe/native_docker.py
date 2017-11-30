import ast
import subprocess
import time

from server.common import common_functions
from server.common import constants
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import container as cont_db
import server.server_plugins.coe_base as coe_base

fmlogger = fm_logger.Logging()


class NativeDockerHandler(coe_base.COEBase):

    def __init__(self):
        self.docker_handler = docker_lib.DockerLib()

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
                    port = parts[1].replace('"', "").rstrip().lstrip()
                    if port and port != 'null':
                        break
        except Exception as e:
            fmlogger.error(e)

        return port

    def _deploy_app_container(self, cont_name, env_vars, app_info):
        app_url = ''

        err, cont_id = self.docker_handler.run_container_with_env(cont_name, env_vars)

        if err:
            fmlogger.debug("Encountered error in deploying application container:%s. Returning." % cont_name)
            return cont_id, app_url, app_status

        app_ip_addr = 'localhost'
        app_port = self._parse_app_port(cont_id)

        app_url = ("http://{app_ip_addr}:{app_port}").format(app_ip_addr=app_ip_addr,
                                                             app_port=app_port)
        fmlogger.debug("App URL: %s" % app_url)
        return cont_id, app_url
    
    def _check_app_status(self, app_url):
        app_status = ''
        if common_functions.is_app_ready(app_url):
            fmlogger.debug("Application is ready.")
            app_status = constants.APP_DEPLOYMENT_COMPLETE
        else:
            fmlogger.debug("Application could not start properly.")
            app_status = constants.APP_DEPLOYMENT_TIMEOUT
        return app_status

    def create_cluster(self, env_id, env_info):
        fmlogger.debug("Creating GKE cluster.")
        cluster_status = 'available'
        return cluster_status

    def delete_cluster(self, env_id, env_info, resource_obj):
        fmlogger.debug("Deleting GKE cluster")
        res_db.Resource().delete(resource_obj.id)

    def deploy_application(self, app_id, app_info):
        fmlogger.debug("Deploying application %s %s" % (app_id, app_info['app_name']))

        env_vars = common_functions.resolve_environment(app_id, app_info)

        cont_name = common_functions.get_image_uri(app_info)
        app_db.App().update(app_id, {'status': constants.DEPLOYING_APP})
        
        cont_id, app_url = self._deploy_app_container(cont_name, env_vars, app_info)
        
        app_data = {}
        app_data['url'] = app_url
        app_data['cont_id'] = cont_id.strip()
        app_data['app_folder_name'] = app_info['app_folder_name']
        app_data['env_name'] = app_info['env_name']

        app_db.App().update(app_id, {'output_config': str(app_data)})

        app_status = self._check_app_status(app_url)

        app_db.App().update(app_id, {'status': app_status,'output_config': str(app_data)})
        fmlogger.debug("Done deploying application")

    def redeploy_application(self, app_id, app_info):
        pass

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting application %s %s" % (app_id, app_info['app_name']))
        try:
            app_db.App().update(app_id, {'status': constants.DELETING_APP})
            app_obj = app_db.App().get(app_id)
            output_config = ast.literal_eval(app_obj.output_config)
            cont_id = output_config['cont_id'].strip()
            err, output = self.docker_handler.stop_container(cont_id)
            if err:
                fmlogger.debug("Encountered error in stopping container %s." % cont_id)
            self.docker_handler.remove_container(cont_id)
        except Exception as e:
            fmlogger.error(e)

        app_db.App().delete(app_id)
        fmlogger.debug("Done deleting application")

    def get_logs(self, app_id, app_info):
        fmlogger.debug("Retrieving logs for application %s %s" % (app_id, app_info['app_name']))

        app_obj = app_db.App().get(app_id)
        output_config = ast.literal_eval(app_obj.output_config)
        cont_id = output_config['cont_id'].strip()

        logs = self.docker_handler.get_logs(cont_id)

        all_lines = []
        for log_line in logs:
            lines = log_line.split('\n')
            all_lines.extend(lines)

        return all_lines