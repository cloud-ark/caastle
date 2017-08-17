import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server


class AppDelete(Command):
    
    def get_parser(self, prog_name):
        parser = super(AppDelete, self).get_parser(prog_name)

        parser.add_argument('app_id')

        return parser

    def take_action(self, parsed_args):
        app_id = parsed_args.app_id

        response = server.TakeAction().delete_app(app_id)