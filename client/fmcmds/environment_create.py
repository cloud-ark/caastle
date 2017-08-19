import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server

env_file_request_string = "Name of yaml file containing environment resource specification"

class EnvironmentCreate(Command):
    
    def get_parser(self, prog_name):
        parser = super(EnvironmentCreate, self).get_parser(prog_name)

        parser.add_argument(dest='env_name',
                            help="Name that you want to give to the environment")

        parser.add_argument(dest='file_name',
                            help=env_file_request_string)

        return parser

    # Template of how to load plugins -- Currently not required
    def _load_plugins(self):
        plugin_list = []
        fp = open("/etc/firstmile/firstmile-client.conf", "r")
        lines = fp.readlines()
        for line in lines:
            if line.find("clients=") >=0:
                pluginList = line.split("=")
                plugin_list = pluginList[1].split(",")

        print("Plugin list:%s" % plugin_list)
        for plugin in plugin_list:
            plugin_class = locate(plugin)
            plugin_class.verify_cli_options()

    def take_action(self, parsed_args):
        
        env_name = parsed_args.env_name
        if not env_name:
            env_name = raw_input("Please enter name for the environment>")
      
        file_name = parsed_args.file_name
        if not file_name:
            file_name = raw_input("Please enter " + env_file_request_string + ">")
        
        try:
            fp = open(file_name, "r")
        except Exception as e:
            print(e)
            exit()

        environment_def = ''
        try:
            environment_def = yaml.load(fp.read())
            #TODO: Verify that each resource definition contains the 'type' attribute
        except Exception as exp:
            print("Error parsing %s" % file_name)
            print(exp)
            exit()

        self.dep_track_url = server.TakeAction().create_environment(env_name, environment_def)

        l = self.dep_track_url.rfind("/")
        env_id = self.dep_track_url[l+1:]
        print("env id:%s" % env_id)


