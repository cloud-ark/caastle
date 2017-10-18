import ast
import time

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

import server.server_plugins.resource_base as resource_base
from server.common import fm_logger
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db

fmlogger = fm_logger.Logging()


class CloudSQLResourceHandler(resource_base.ResourceBase):
    """CloudSQL Resource handler."""

    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('sqladmin', 'v1beta4',
                              credentials=credentials)

    def __init(self):
        pass

    def create(self, env_id, resource_details):
        fmlogger.debug("CloudSQL create")

        env_obj = env_db.Environment().get(env_id)
        res_type = resource_details['type']
        project_name = resource_details['project']

        env_output_config = ast.literal_eval(env_obj.output_config)
        env_version_stamp = env_output_config['env_version_stamp']

        instance_id = env_obj.name + "-" + env_version_stamp

        database_instance_body = {
            'name': instance_id,
            'settings': {'tier': 'db-n1-standard-1'},
        }

        create_request = CloudSQLResourceHandler.service.instances().insert(
            project=project_name,
            body=database_instance_body
        )

        res_id = ''
        res_data = {}
        try:
            create_response = create_request.execute()
            res_data['env_id'] = env_id
            res_data['cloud_resource_id'] = instance_id
            res_data['type'] = res_type
            res_data['status'] = 'creating'

            detailed_description = {}
            detailed_description['create_response'] = create_response
            detailed_description['name'] = instance_id
            detailed_description['project'] = project_name
            res_data['detailed_description'] = str(detailed_description)
            import pdb; pdb.set_trace()
            res_id = res_db.Resource().insert(res_data)
        except Exception as e:
            fmlogger.error("Exception encountered in creating CloudSQL instance %s" % e)

        available = False
        timeout = 100
        i = 0
        while not available and i < timeout:
            get_request = CloudSQLResourceHandler.service.instances().get(
                project=project_name,
                instance=instance_id
            )
            get_response = get_request.execute()
            status = get_response['state']

            res_data['status'] = status
            res_db.Resource().update(res_id, res_data)
            if status == 'RUNNABLE':
                break
            else:
                i = i + 1
                time.sleep(2)

        fmlogger.debug("Exiting CloudSQL create call.")

    def delete(self, request_obj):
        fmlogger.debug("CloudSQL delete.")

        res_data = {}       
        res_data['status'] = 'deleting'
        res_db.Resource().update(request_obj.id, res_data)

        detailed_description = ast.literal_eval(request_obj.detailed_description)

        name = detailed_description['name']
        project_name = detailed_description['project']

        delete_request = CloudSQLResourceHandler.service.instances().delete(
                project=project_name,
                instance=name
        )

        delete_request.execute()

        gone = False
        while not gone:
          try:
            get_request = CloudSQLResourceHandler.service.instances().get(
                project=project_name,
                instance=name
            )
            get_response = get_request.execute()              
          except Exception as e:
              fmlogger.error("Encountered exception in cloudsql delete.")
              gone = True

        res_db.Resource().delete(request_obj.id)
