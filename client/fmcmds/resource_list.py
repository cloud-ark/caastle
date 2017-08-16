import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server


class ResourceList(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceList, self).get_parser(prog_name)

        return parser

    def take_action(self, parsed_args):
        response = server.TakeAction().get_resources()
        print(response)