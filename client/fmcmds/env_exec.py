import ast
import json
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

        response = server.TakeAction().get_environment(env_name)
        if response:
            response_json = json.loads(response)
            env_output_config = ast.literal_eval(response_json['data']['env_definition'])
            type = env_output_config['environment']['app_deployment']['type']
            if type == 'local-docker':
                print("Shell functionality not available for local deployment target.")
                print("You can use docker commands from command-line instead.")
                exit()
            if response_json['data']['status'] == 'available':
                print("Running the command %s on the environment..." % command_string)
                response = server.TakeAction().run_command(env_name, command_string)
                print(response)
            else:
                print("Environment %s is not in appropriate state." % env_name)
