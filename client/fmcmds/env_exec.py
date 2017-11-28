from cliff.command import Command

import call_server as server

class EnvironmentExec(Command):
    
    def get_parser(self, prog_name):
        parser = super(EnvironmentExec, self).get_parser(prog_name)

        parser.add_argument(dest='env_name',
                            help="Environment name")
        
        parser.add_argument(dest='command_string',
                            help="Command string (in single quotes)")

        return parser

    def take_action(self, parsed_args):
        env_name = parsed_args.env_name
        
        command_string = parsed_args.command_string

        response = server.TakeAction().run_command(env_name, command_string)
        print(response)
