import os

from cliff.command import Command

import call_server as server
import common


class AppDeploy(Command):

    def get_parser(self, prog_name):
        parser = super(AppDeploy, self).get_parser(prog_name)

        parser.add_argument('app_name',
                            help="Application name")

        parser.add_argument('env_id',
                            help="Id of the environment on which application should be deployed")

        parser.add_argument('app_file',
                            help="YAML file that specifies application details")

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

        app_yaml = parsed_args.app_file
        app_info['app_yaml'] = app_yaml

        app_location = os.getcwd()
        app_folder_name = common.get_app_folder_name(app_location)
        app_info['app_folder_name'] = app_folder_name
        self.dep_track_url = server.TakeAction().deploy_app(app_location, app_info)

        l = self.dep_track_url.rfind("/")
        app_id = self.dep_track_url[l+1:]
        if app_id:
            print("app id:%s" % app_id)
