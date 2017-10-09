from cliff.command import Command

import call_server as server


class AppShow(Command):
    
    def get_parser(self, prog_name):
        parser = super(AppShow, self).get_parser(prog_name)
        parser.add_argument('app_id')
        return parser

    def take_action(self, parsed_args):
        app_id = parsed_args.app_id

        response = server.TakeAction().get_app(app_id)
        print(response)