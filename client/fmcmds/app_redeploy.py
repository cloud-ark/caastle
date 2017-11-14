import os

from cliff.command import Command

import call_server as server


class AppRedeploy(Command):

    def _get_app_folder_name(self, app_location):
        last_slash_index = app_location.rfind("/")
        app_folder_name = app_location[last_slash_index+1:]
        return app_folder_name

    def get_parser(self, prog_name):
        parser = super(AppRedeploy, self).get_parser(prog_name)

        parser.add_argument('app_name')
        return parser

    def take_action(self, parsed_args):
        app_name = parsed_args.app_name

        app_info = {}
        app_location = os.getcwd()
        app_folder_name = self._get_app_folder_name(app_location)
        app_info['app_folder_name'] = app_folder_name
        server.TakeAction().redeploy_app(app_location, app_info, app_names)
