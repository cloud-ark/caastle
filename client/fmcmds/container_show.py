from cliff.command import Command

import call_server as server


class ContainerShow(Command):
    
    def get_parser(self, prog_name):
        parser = super(ContainerShow, self).get_parser(prog_name)
        parser.add_argument('container_name')
        return parser

    def take_action(self, parsed_args):
        container_name = parsed_args.container_name

        response = server.TakeAction().get_container(container_name)
        print(response)
