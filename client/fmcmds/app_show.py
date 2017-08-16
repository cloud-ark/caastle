import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server


class AppShow(Command):
    
    def get_parser(self, prog_name):
        parser = super(AppShow, self).get_parser(prog_name)

        parser.add_argument('--app-id',
                            dest='app_id',
                            help="App id")

        return parser

    def take_action(self, parsed_args):
        app_id = parsed_args.app_id

        if not app_id:
            app_id = raw_input("Enter app id>")
        response = server.TakeAction().get_app(app_id)
        print(response)