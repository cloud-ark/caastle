import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server

class ResourceCreate(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceCreate, self).get_parser(prog_name)

        parser.add_argument('--type',
                            dest='resource_type',
                            help="Resource type: rds (for RDS database), dynamodb (for DynamoDB table), sqs (for SQS queue)")
        
        parser.add_argument('--name',
                            dest='resource_name',
                            help="Resource name: Name for RDS database, Name for DynamoDB table, Name for SQS queue")

        return parser

    def take_action(self, parsed_args):
        type = parsed_args.resource_type
        name = parsed_args.resource_name
        resource_obj = {}
        resource_obj['resource_type'] = type
        resource_obj['name'] = name
        resource_obj['configuration'] = {} # provision to pass customized configuration options as a dict
        resource_obj['artifact_type'] = 'resource'
        resource_obj['action'] = 'create'
        resource_id = server.TakeAction().create_resource(resource_obj)
        print("Resource ID:%s" % resource_id)
