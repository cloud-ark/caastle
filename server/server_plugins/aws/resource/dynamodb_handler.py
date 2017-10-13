import boto3
import time

import server.server_plugins.resource_base as resource_base
from server.common import constants
from server.common import fm_logger
# from server.dbmodule import db_handler

TIMEOUT_COUNT = 400

fmlogger = fm_logger.Logging()


class DynamoDBResourceHandler(resource_base.ResourceBase):

    def __init__(self):
        self.client = boto3.client('dynamodb')
    
    def create(self, request_obj):
        table_name = request_obj['name']
        attribute_definitions = []
        if 'attribute_definitions' in request_obj:
            attribute_definitions = request_obj['attribute_definitions']
        else:
            attribute_definitions = [{'AttributeName': 'PrimaryKey', 'AttributeType': 'N'},
                                     {'AttributeName': 'StringData', 'AttributeType': 'S'}]
        key_schema = []
        if 'key_schema' in request_obj:
            key_schema = request_obj['key_schema']
        else:
            key_schema = [{'AttributeName': 'PrimaryKey', 'KeyType': 'HASH'},
                          {'AttributeName': 'StringData', 'KeyType': 'RANGE'}]

        provisioned_throughput = {'ReadCapacityUnits': 1,
                                  'WriteCapacityUnits': 1}
        try:
            response = self.client.create_table(AttributeDefinitions=attribute_definitions,
                                                TableName=table_name,
                                                KeySchema=key_schema,
                                                ProvisionedThroughput=provisioned_throughput)
            fmlogger.debug(response)
        except Exception as e:
            fmlogger.error(e)
        
        # wait for few seconds for create_table action to take effect
        time.sleep(5)

        status = ''
        count = 1
        while count < constants.TIMEOUT_COUNT and status.lower() is not 'active':
            status_dict = self.client.describe_table(TableName=table_name)
            status = status_dict['Table']['TableStatus']
            # db_handler.DBHandler().update_resource(request_obj['resource_id'], status)
            count = count + 1
            time.sleep(2)

        return status
        
    def delete(self, request_obj):
        table_name = request_obj['name']
        try:
            response = self.client.delete_table(TableName=table_name)
            fmlogger.debug(response)
        except Exception as e:
            fmlogger.error(e)
            # db_handler.DBHandler().delete_resource(request_obj['resource_id'])
            return

        deleted = False
        count = 1
        while count < constants.TIMEOUT_COUNT and not deleted:
            try:
                status_dict = self.client.describe_table(TableName=table_name)
                status = status_dict['Table']['TableStatus']
                fmlogger.debug(status)
                # db_handler.DBHandler().update_resource(request_obj['resource_id'], status)
                count = count + 1
                time.sleep(2)
            except Exception as e:
                fmlogger.error(e)
                deleted = True
                # db_handler.DBHandler().delete_resource(request_obj['resource_id'])
