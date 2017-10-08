import logging
import prettytable
import os
import yaml

from cliff.command import Command

import call_server as server


class ResourceShow(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceShow, self).get_parser(prog_name)

        parser.add_argument('--resource-id',
                            dest='resource_id',
                            help="Resource id")

        parser.add_argument('--env-id',
                            dest='env_id',
                            help="Environment id")

        return parser

    def take_action(self, parsed_args):
        resource_id = parsed_args.resource_id
        env_id = parsed_args.env_id
        if resource_id:
            response = server.TakeAction().get_resource(resource_id)
        elif env_id:
            response = server.TakeAction().get_resources_for_environment(env_id)
        else:
            print("Either resource-id or env-id should be provided.")
            exit()
        print(response)