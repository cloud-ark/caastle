import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server


class ResourceStackDelete(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceStackDelete, self).get_parser(prog_name)

        parser.add_argument('--stack-id',
                            dest='stack_id',
                            help="Stack id (FIX: does not delete individual resources on target clouds)")

        return parser

    def take_action(self, parsed_args):
        stack_id = parsed_args.stack_id

        response = server.TakeAction().delete_resource_stack(stack_id)
        print(response)