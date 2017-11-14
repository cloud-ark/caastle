import ast
import time

from docker import Client

from server.common import constants
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
import server.server_plugins.resource_base as resource_base

fmlogger = fm_logger.Logging()

DEFAULT_MYSQL_VERSION = 'mysql:5.5'

class MySQLResourceHandler(resource_base.ResourceBase):
    """MySQL Resource handler."""
    
    def __init__(self):
        self.docker_client = Client(base_url='unix://var/run/docker.sock', version='1.18')
        self.docker_handler = docker_lib.DockerLib()

    def create(self, env_id, resource_details):
        fmlogger.debug("MySQL container create")

        res_data = {}
        res_data['status'] = 'unavailable'
        env_obj = env_db.Environment().get(env_id)
        res_type = resource_details['type']
        env_output_config = ast.literal_eval(env_obj.output_config)
        env_version_stamp = env_output_config['env_version_stamp']

        container_name = env_obj.name + "-" + env_version_stamp

        res_id = ''

        res_data['env_id'] = env_id
        res_data['cloud_resource_id'] = container_name
        res_data['type'] = res_type
        res_data['status'] = 'creating'
        res_id = res_db.Resource().insert(res_data)

        env = {"MYSQL_ROOT_PASSWORD": constants.DEFAULT_DB_PASSWORD,
               "MYSQL_DATABASE": constants.DEFAULT_DB_NAME,
               "MYSQL_USER": constants.DEFAULT_DB_USER,
               "MYSQL_PASSWORD": constants.DEFAULT_DB_PASSWORD}

        self.docker_client.import_image(image=DEFAULT_MYSQL_VERSION)
        serv_cont = self.docker_client.create_container(DEFAULT_MYSQL_VERSION,
                                                        detach=True,
                                                        environment=env,
                                                        name=container_name)
        self.docker_client.start(serv_cont)

        cont_data = self.docker_client.inspect_container(serv_cont)

        service_ip_addr = cont_data['NetworkSettings']['IPAddress']
        container_id = cont_data['Id']
        fmlogger.debug("MySQL Service IP Address:%s" % service_ip_addr)

        filtered_description = {}
        detailed_description = {}
        filtered_description['Username'] = constants.DEFAULT_DB_USER
        filtered_description['Password'] = constants.DEFAULT_DB_PASSWORD
        filtered_description['Root_Password'] = constants.DEFAULT_DB_PASSWORD
        filtered_description['DBName'] = constants.DEFAULT_DB_NAME
        filtered_description['DBHOST'] = service_ip_addr
        detailed_description['container_id'] = container_id
        detailed_description['container_name'] = container_name
        res_data['detailed_description'] = str(detailed_description)
        res_data['filtered_description'] = str(filtered_description)
        res_data['status'] = 'available'
        res_db.Resource().update(res_id, res_data)

        return res_data['status']

    def delete(self, request_obj):
        fmlogger.debug("CloudSQL delete.")

        res_data = {}
        res_data['status'] = 'deleting'

        detailed_description = ast.literal_eval(request_obj.detailed_description)
        container_id = detailed_description['container_id']
        container_name = detailed_description['container_name']

        try:
            self.docker_handler.stop_container(container_id)
            self.docker_handler.remove_container(container_id)
        except Exception as e:
            fmlogger.error(e)
        else:
            self.docker_handler.remove_container_image(container_name)

        # stop container
        res_db.Resource().delete(request_obj.id)
