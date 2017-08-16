import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server


class ResourceDelete(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceDelete, self).get_parser(prog_name)

        parser.add_argument('--resource-id',
                            dest='resource_id',
                            help="Resource id")

        return parser

    def take_action(self, parsed_args):
        resource_id = parsed_args.resource_id

        response = server.TakeAction().delete_resource(resource_id)
        print(response)