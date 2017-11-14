from cliff.command import Command

import call_server as server


class ContainerList(Command):
    
    def get_parser(self, prog_name):
        parser = super(ContainerList, self).get_parser(prog_name)

        return parser

    def take_action(self, parsed_args):
        response = server.TakeAction().get_container_list()
        print(response)
