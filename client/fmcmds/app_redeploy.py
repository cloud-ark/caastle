import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server


class AppRedeploy(Command):

    def _get_app_folder_name(self, app_location):
        last_slash_index = app_location.rfind("/")
        app_folder_name = app_location[last_slash_index+1:]
        return app_folder_name

    def get_parser(self, prog_name):
        parser = super(AppRedeploy, self).get_parser(prog_name)

        parser.add_argument('--app-id',
                            dest='app_id',
                            help="App id")
        
        parser.add_argument('--env-id',
                            dest='env_id',
                            help="Environment id")
        return parser

    def take_action(self, parsed_args):
        app_id = parsed_args.app_id

        if not app_id:
            app_id = raw_input("Enter app id>")
        
        env_id = parsed_args.env_id
        
        app_info = {}
        app_info['env_id'] = env_id
        app_location = os.getcwd()
        app_folder_name = self._get_app_folder_name(app_location)
        app_info['app_folder_name'] = app_folder_name
        response = server.TakeAction().redeploy_app(app_location, app_info, app_id)
        print(response)