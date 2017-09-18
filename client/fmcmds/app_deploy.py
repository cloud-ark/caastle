import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server


class AppDeploy(Command):

    def _get_app_folder_name(self, app_location):
        last_slash_index = app_location.rfind("/")
        app_folder_name = app_location[last_slash_index+1:]
        return app_folder_name

    def get_parser(self, prog_name):
        parser = super(AppDeploy, self).get_parser(prog_name)

        parser.add_argument('app_name',
                            help="Application name")

        parser.add_argument('env_id',
                            help="Id of the environment to which application should be bound")

        parser.add_argument('--memory',
                            help="Memory in MB to be given to the application container at runtime")

        parser.add_argument('--port',
                            help="Application port (default port 80)")

        return parser

    def take_action(self, parsed_args):
        app_info = {}
        app_name = parsed_args.app_name
        if not app_name:
            app_name = raw_input("Please enter name for the application>")
        app_info['app_name'] = app_name

        env_id = parsed_args.env_id
        if env_id:
            app_info['env_id'] = env_id

        app_port = '80'
        if parsed_args.port:
            app_port = parsed_args.port
        app_info['app_port'] = app_port

        if parsed_args.memory:
            app_info['memory'] = parsed_args.memory

        app_location = os.getcwd()
        app_folder_name = self._get_app_folder_name(app_location)
        app_info['app_folder_name'] = app_folder_name
        self.dep_track_url = server.TakeAction().deploy_app(app_location, app_info)

        l = self.dep_track_url.rfind("/")
        app_id = self.dep_track_url[l+1:]
        if app_id:
            print("app id:%s" % app_id)
