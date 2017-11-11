import ast
import boto3
import time

import server.server_plugins.resource_base as resource_base
from server.common import constants
from server.common import fm_logger
from server.dbmodule.objects import container as cont_db
from server.server_plugins.aws import aws_helper

fmlogger = fm_logger.Logging()


class ECRHandler(resource_base.ResourceBase):
    """ECR Resource handler."""

    awshelper = aws_helper.AWSHelper()

    def __init__(self):
        self.client = boto3.client('ecr')

    def create(self, cont_name, cont_info):
        pass

    def delete(self, cont_name, cont_info):
        pass
