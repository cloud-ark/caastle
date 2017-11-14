from cliff.command import Command

import call_server as server


class ResourceShow(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceShow, self).get_parser(prog_name)

        #parser.add_argument('--resource-id',
        #                    dest='resource_id',
        #                    help="Resource id")

        parser.add_argument('env_name',
                            help="Environment name")

        return parser

    def take_action(self, parsed_args):
        #resource_id = parsed_args.resource_id
        env_name = parsed_args.env_name
        #if resource_id:
        #    response = server.TakeAction().get_resource(resource_id)
        #env_name:
        response = server.TakeAction().get_resources_for_environment(env_name)
        #else:
        #    print("Either resource-id or env-id should be provided.")
        #    exit()
        print(response)
