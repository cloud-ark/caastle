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

        parser.add_argument('--name',
                            dest='app_name',
                            help="Application name")
        
        parser.add_argument('--target',
                            dest='target',
                            help="Application deployment target (local | aws)")

        parser.add_argument('--env-id',
                            dest='env_id',
                            help="Id of the environment on which to deploy the application")

        return parser

    def take_action(self, parsed_args):
        app_info = {}        
        app_name = parsed_args.app_name
        if not app_name:
            app_name = raw_input("Please enter name for the application>")
        app_info['app_name'] = app_name

        target = parsed_args.target
        if not target:
            target = raw_input("Please enter application deployment target>")
        app_info['target'] = target

        env_id = parsed_args.env_id
        if env_id:
            app_info['env_id'] = env_id

        app_port = raw_input("Please enter application port>")
        app_info['app_port'] = app_port

        app_location = os.getcwd()
        app_folder_name = self._get_app_folder_name(app_location)
        app_info['app_folder_name'] = app_folder_name
        self.dep_track_url = server.TakeAction().deploy_app(app_location, app_info)
        print("Application deployment tracking url:%s" % self.dep_track_url)

        l = self.dep_track_url.rfind("/")
        dep_id = self.dep_track_url[l+1:]
        print("dep id:%s" % dep_id)