import ast
import boto3
import time

from common import constants
from common import fm_logger
from dbmodule import db_handler

from server.server_plugins.aws import aws_helper

fmlogger = fm_logger.Logging()

DEFAULT_RDS_ENGINE = 'mysql'
DEFAULT_RDS_INSTANCE_CLASS = 'db.t1.micro'  

dbhandler = db_handler.DBHandler()

class RDSResourceHandler(object):
    
    awshelper = aws_helper.AWSHelper()

    def __init__(self):
        self.client = boto3.client('rds')
    
    def create(self, env_id, resource_details):
        env_obj = dbhandler.get_environment(env_id)
        res_type = resource_details['type']
        now = time.time()
        ts = str(now).split(".")[0]
        #instance_id = "env-" + str(env_id) + "-" + res_type + "-" + ts

        env_output_config = ast.literal_eval(env_obj[db_handler.ENV_OUTPUT_CONFIG])
        env_version_stamp = env_output_config['env_version_stamp']

        instance_id = env_obj[db_handler.ENV_NAME] + "-" + env_version_stamp
        db_name = constants.DEFAULT_DB_NAME
        response = ''

        vpc_id = ''
        vpc_traffic_block = ''        
        if 'vpc_id' in env_output_config and 'cidr_block' in env_output_config:
            vpc_id = env_output_config['vpc_id']
            vpc_traffic_block = env_output_config['cidr_block']
        else:
            vpc_details = RDSResourceHandler.awshelper.get_vpc_details()
            vpc_id = vpc_details['vpc_id']
            vpc_traffic_block = vpc_details['cidr_block']

        #env_sec_group = RDSResourceHandler.awshelper.create_security_group_for_vpc(vpc_id, '')
        #env_sec_group = 'sg-687f8412'
        sec_group_name = instance_id + "-sql"
        sec_group_id = RDSResourceHandler.awshelper.create_security_group_for_vpc(vpc_id, sec_group_name)

        port_list = [3306]
        RDSResourceHandler.awshelper.setup_security_group(vpc_id, vpc_traffic_block,
                                                  sec_group_id, sec_group_name, port_list)
        
        publicly_accessible = False
        if 'policy' in resource_details:
            if resource_details['policy']['access'] == 'open':
                publicly_accessible = True
        try:
            response = self.client.create_db_instance(DBName=db_name,
                                                      DBInstanceIdentifier=instance_id,
                                                      DBInstanceClass=DEFAULT_RDS_INSTANCE_CLASS,
                                                      Engine=DEFAULT_RDS_ENGINE,
                                                      MasterUsername=constants.DEFAULT_DB_USER,
                                                      MasterUserPassword=constants.DEFAULT_DB_PASSWORD,
                                                      PubliclyAccessible=publicly_accessible,
                                                      AllocatedStorage=5,
                                                      VpcSecurityGroupIds=[sec_group_id],
                                                      Tags=[{"Key":"Tag1", "Value":"Value1"}])
        except Exception as e:
            fmlogger.error(e)
            print(e)

        status = constants.CREATION_REQUEST_RECEIVED
        count = 1

        instance_description = ''
        filtered_description = dict()
        res_id = db_handler.DBHandler().add_resource(env_id, instance_id, res_type, status)
        while count < constants.TIMEOUT_COUNT and status.lower() is not 'available':
            instance_description = self.client.describe_db_instances(DBInstanceIdentifier=instance_id)
            status = instance_description['DBInstances'][0]['DBInstanceStatus']
            
            if status.lower() == 'available':
                break

            db_handler.DBHandler().update_resource(res_id, status=status,
                                                   filtered_description=str(filtered_description),
                                                   detailed_description=str(instance_description))
            count = count + 1
            time.sleep(2)

        filtered_description['DBInstanceIdentifier'] = instance_id
        filtered_description['DBInstanceClass'] = DEFAULT_RDS_INSTANCE_CLASS
        filtered_description['Engine'] = DEFAULT_RDS_ENGINE
        filtered_description['MasterUsername'] = constants.DEFAULT_DB_USER
        filtered_description['MasterUserPassword'] = constants.DEFAULT_DB_PASSWORD
        filtered_description['DBName'] = constants.DEFAULT_DB_NAME
        endpoint_address = instance_description['DBInstances'][0]['Endpoint']['Address']
        filtered_description['Address'] = endpoint_address

        db_handler.DBHandler().update_resource(res_id, status=status,
                                               filtered_description=str(filtered_description),
                                               detailed_description=str(instance_description))
        
        return status.lower()

    def delete(self, request_obj):
        db_name = instance_id = request_obj['name']
        
        try:
            response = self.client.delete_db_instance(DBInstanceIdentifier=instance_id,
                                                      SkipFinalSnapshot=True)
        except Exception as e:
            fmlogger.error(e)
            db_handler.DBHandler().delete_resource(request_obj['resource_id'])
            
        deleted = False
        count = 1
        while count < constants.TIMEOUT_COUNT and not deleted:
            try:
                status_dict = self.client.describe_db_instances(DBInstanceIdentifier=instance_id)
                status = status_dict['DBInstances'][0]['DBInstanceStatus']
                db_handler.DBHandler().update_resource(request_obj['resource_id'], status)
                count = count + 1
                time.sleep(2)
            except Exception as e:
                fmlogger.error(e)
                deleted = True
                db_handler.DBHandler().delete_resource(request_obj['resource_id'])

class RDS():
    @staticmethod
    def verify_cli_options(self):
        print("Verifying CLI Options for RDS")