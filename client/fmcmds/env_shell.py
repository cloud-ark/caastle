import json
import readline

from cliff.command import Command

import call_server as server

class EnvironmentShell(Command):

    def get_parser(self, prog_name):
        parser = super(EnvironmentShell, self).get_parser(prog_name)

        parser.add_argument(dest='env_name',
                            help="Environment name")

        return parser

    def take_action(self, parsed_args):
        env_name = parsed_args.env_name

        response = server.TakeAction().get_environment(env_name)
        if response:
            response_json = json.loads(response)
            if response_json['data']['status'] == 'available':
                while True:
                    command_string = raw_input('("exit" to quit, "help" to see commands) cld>')
                    command_string = command_string.strip()
                    if command_string == 'exit':
                        break
                    response = server.TakeAction().run_command(env_name, command_string)
                    print(response)
            else:
                print("Environment %s is not in appropriate state." % env_name)
