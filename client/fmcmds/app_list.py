from cliff.command import Command

import call_server as server


class AppList(Command):
    
    def get_parser(self, prog_name):
        parser = super(AppList, self).get_parser(prog_name)

        return parser

    def take_action(self, parsed_args):
        response = server.TakeAction().get_app_list()
        print(response)