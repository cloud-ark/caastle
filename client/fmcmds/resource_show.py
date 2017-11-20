from cliff.command import Command

import call_server as server


class ResourceShow(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceShow, self).get_parser(prog_name)

        parser.add_argument('env_name',
                            help="Environment name")

        return parser

    def take_action(self, parsed_args):
        env_name = parsed_args.env_name
        response = server.TakeAction().get_resources_for_environment(env_name)
        print(response)
