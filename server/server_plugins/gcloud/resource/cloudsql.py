import ast
import re
import time

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from server.common import constants
from server.common import fm_logger
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
import server.server_plugins.resource_base as resource_base
from server.server_plugins.gcloud import gcloud_helper

fmlogger = fm_logger.Logging()


class CloudSQLResourceHandler(resource_base.ResourceBase):
    """CloudSQL Resource handler."""

    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('sqladmin', 'v1beta4',
                              credentials=credentials,
                              cache_discovery=False)

    gcloudhelper = gcloud_helper.GCloudHelper()

    allowed_commands = ["gcloud sql instances list*",
                        "gcloud sql instances describe*"
                       ]

    help_commands = ["gcloud sql instances list ",
                     "gcloud sql instances describe ",
                    ]

    def __init(self):
        pass

    def _verify(self, command):
        matched = None
        for pattern in CloudSQLResourceHandler.allowed_commands:
            p = re.compile(pattern, re.IGNORECASE)
            matched = p.match(command)
            if matched:
                return True
        return False

    def _create_database(self, resource_details, project_name,
                         instance_id, etag):
        dbname = constants.DEFAULT_DB_NAME

        if 'configuration' in resource_details:
            if 'dbname' in resource_details['configuration']:
                dbname = resource_details['configuration']['dbname']

        db_body = {
            'name': dbname,
            'project': project_name,
            'instance': instance_id,
            'etag': etag
        }

        insert_db_req = CloudSQLResourceHandler.service.databases().insert(
            project=project_name,
            instance=instance_id,
            body=db_body
        )

        create_accepted = False
        count = 1
        while not create_accepted:
            try:
                insert_db_req.execute()
                create_accepted = True
            except Exception as e:
                fmlogger.error("Encountered exception when creating database %s" % e)
                time.sleep(2)
                count = count + 1

        if not create_accepted:
            raise Exception("DB create action encountered exception.")

        # Allow Google to create the database
        time.sleep(5)

        return dbname

    def create(self, env_id, resource_details):
        fmlogger.debug("CloudSQL create")

        cloudsql_status = 'unavailable'
        env_obj = env_db.Environment().get(env_id)
        res_type = resource_details['type']

        env_details = ast.literal_eval(env_obj.env_definition)
        project_name = env_details['environment']['app_deployment']['project']

        env_output_config = ast.literal_eval(env_obj.output_config)
        env_version_stamp = env_output_config['env_version_stamp']

        instance_id = env_obj.name + "-" + env_version_stamp

        authorizedNetworks = ''

        if 'policy' in resource_details:
            if resource_details['policy']['access'] == 'open':
                authorizedNetworks = '0.0.0.0/0'
        if 'cluster_ips' in env_output_config:
            cluster_ip_list = env_output_config['cluster_ips']
            authorizedNetworks = ','.join(cluster_ip_list)

        database_instance_body = {}
        if authorizedNetworks:
            database_instance_body = {
                'name': instance_id,
                'settings': {'tier': 'db-n1-standard-1',
                             'ipConfiguration': {
                                 'authorizedNetworks': [{'value': authorizedNetworks}]}},
            }
        else:
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
        res_data['env_id'] = env_id
        res_data['cloud_resource_id'] = instance_id
        res_data['type'] = res_type
        res_data['status'] = 'creating'
        res_id = res_db.Resource().insert(res_data)

        try:
            create_response = create_request.execute()
            detailed_description = {}
            detailed_description['action_response'] = create_response
            detailed_description['name'] = instance_id
            detailed_description['project'] = project_name
            res_data['detailed_description'] = str(detailed_description)
            res_db.Resource().update(res_id, res_data)
        except Exception as e:
            fmlogger.error("Exception encountered in creating CloudSQL instance %s" % e)
            res_data['status'] = 'Error: ' + str(e)
            res_db.Resource().update(res_id, res_data)
            return cloudsql_status

        available = False
        i = 0
        etag = ''

        filtered_description = {}
        get_response = ''
        while not available:
            get_request = CloudSQLResourceHandler.service.instances().get(
                project=project_name,
                instance=instance_id
            )
            get_response = ''
            try:
                get_response = get_request.execute()
            except Exception as e:
                fmlogger.error(e)
                res_data['status'] = str(e)
                res_db.Resource().update(res_id, res_data)
                return cloudsql_status

            status = get_response['state']
            etag = get_response['etag']

            res_data['status'] = status
            detailed_description['etag'] = etag
            res_data['detailed_description'] = str(detailed_description)

            res_db.Resource().update(res_id, res_data)
            if status == 'RUNNABLE':
                cloudsql_status = 'available'
                available = True
            else:
                i = i + 1
                time.sleep(3)

        if i == constants.TIMEOUT_COUNT:
            res_data['status'] = 'creation-timed-out'
            res_db.Resource().update(res_id, res_data)
            return cloudsql_status

        detailed_description['action_response'] = get_response
        filtered_description['Address'] = get_response['ipAddresses'][0]['ipAddress']

        username = constants.DEFAULT_DB_USER
        if 'username' in resource_details:
            username = resource_details['username']
        password = constants.DEFAULT_DB_PASSWORD
        if 'password' in resource_details:
            password = resource_details['password']

        user_body = {
            'name': username,
            'project': project_name,
            'instance': instance_id,
            'password': password,
            'etag': etag
        }
        insert_user_req = CloudSQLResourceHandler.service.users().insert(
            project=project_name,
            instance=instance_id,
            body=user_body
        )

        insert_user_req.execute()

        # Give some time for Google to create the username/password
        time.sleep(10)

        dbname = ''
        try:
            dbname = self._create_database(resource_details, project_name, instance_id, etag)
        except Exception as e:
            fmlogger.error(e)
            res_data['status'] = str(e)
            cloudsql_status = 'unavailable'

        filtered_description['Username'] = username
        filtered_description['Password'] = password
        filtered_description['DBName'] = dbname
        res_data['filtered_description'] = str(filtered_description)
        res_data['detailed_description'] = str(detailed_description)
        res_db.Resource().update(res_id, res_data)

        fmlogger.debug("Exiting CloudSQL create call.")
        return cloudsql_status

    def delete(self, request_obj):
        fmlogger.debug("CloudSQL delete.")

        res_data = {}
        res_data['status'] = 'deleting'
        res_db.Resource().update(request_obj.id, res_data)

        try:
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
                    get_request.execute()
                except Exception as e:
                    fmlogger.error("Encountered exception in cloudsql delete %s" % e)
                    gone = True
        except Exception as e:
            fmlogger.error(e)

        res_db.Resource().delete(request_obj.id)


    def run_command(self, env_id, env_name, resource_obj, command):
        fmlogger.debug("Running command %s " % command)

        if command.lower() == 'help':
            return CloudSQLResourceHandler.help_commands

        command_output = ''

        is_supported_command = self._verify(command)
        if not is_supported_command:
            command_output = ["Command not supported"]
            return command_output

        base_command = ''
        instance_name = resource_obj.cloud_resource_id

        user_account, project_name, zone_name = CloudSQLResourceHandler.gcloudhelper.get_deployment_details(env_id)

        base_command = ""
        base_image = "google"
        command = "/google-cloud-sdk/bin/" + command
        command_output = CloudSQLResourceHandler.gcloudhelper.run_command(env_id,
                                                                          env_name,
                                                                          resource_obj,
                                                                          base_command,
                                                                          command,
                                                                          base_image)

        output_lines = command_output.split("\n")

        return output_lines
