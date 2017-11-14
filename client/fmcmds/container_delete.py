from cliff.command import Command

import call_server as server


class ContainerDelete(Command):
    
    def get_parser(self, prog_name):
        parser = super(ContainerDelete, self).get_parser(prog_name)

        parser.add_argument('cont_name')

        return parser

    def take_action(self, parsed_args):
        cont_name = parsed_args.cont_name

        server.TakeAction().delete_container(cont_name)
