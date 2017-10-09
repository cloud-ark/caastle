from cliff.command import Command

import call_server as server


class EnvironmentList(Command):
    
    def get_parser(self, prog_name):
        parser = super(EnvironmentList, self).get_parser(prog_name)

        return parser

    def take_action(self, parsed_args):
        response = server.TakeAction().get_environment_list()
        print(response)