from cliff.command import Command

import call_server as server


class EnvironmentShow(Command):
    
    def get_parser(self, prog_name):
        parser = super(EnvironmentShow, self).get_parser(prog_name)

        parser.add_argument(dest='env_name',
                            help="Environment name")

        return parser

    def take_action(self, parsed_args):
        env_name = parsed_args.env_name

        response = server.TakeAction().get_environment(env_name)
        print(response)
