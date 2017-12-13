import os
import yaml

from cliff.command import Command

import call_server as server
import common


class AppDeploy(Command):

    def get_parser(self, prog_name):
        parser = super(AppDeploy, self).get_parser(prog_name)

        parser.add_argument('app_name',
                            help="Application name")

        parser.add_argument('env_name',
                            help="Name of the environment on which application should be deployed")

        parser.add_argument('app_file',
                            help="YAML file that specifies application details")

        return parser

    def take_action(self, parsed_args):
        app_info = {}
        app_info['app_name'] = parsed_args.app_name
        app_info['env_name'] = parsed_args.env_name
        app_info['app_yaml'] = parsed_args.app_file

        # Check if app_file contains container_port defined or not
        try:
            fp = open(parsed_args.app_file, "r")
            app_def = yaml.load(fp.read())
            if 'app' in app_def:
                if app_def['app'] is None:
                    print("app yaml cannot be empty.")
                    exit()
                if 'container_port' not in app_def['app']:
                    print("'container_port' attribute is missing from app definition.")
                    exit()
                elif 'image' not in app_def['app']:
                    print("'image' attribute is missing from app definition.")
                    exit()
        except Exception as e:
            exit()

        app_location = os.getcwd()
        app_folder_name = common.get_app_folder_name(app_location)
        app_info['app_folder_name'] = app_folder_name
        server.TakeAction().deploy_app(app_location, app_info)
