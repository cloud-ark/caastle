import logging
import prettytable
import os
import yaml

from cliff.command import Command
from pydoc import locate

import call_server as server

resource_file_request_string = "name of yaml file containing resource specifications"

class ResourceStackCreate(Command):
    
    def get_parser(self, prog_name):
        parser = super(ResourceStackCreate, self).get_parser(prog_name)

        parser.add_argument('-f',
                            dest='file_name',
                            help=resource_file_request_string)

        return parser

    def take_action(self, parsed_args):
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
        
        file_name = parsed_args.file_name
        if not file_name:
            file_name = raw_input("Please enter " + resource_file_request_string + " >")
        
        fp = open(file_name, "r")

        resource_obj = ''
        try:
            resource_obj = yaml.load(fp.read())
            print(resource_obj)
        except Exception as exp:
            print("Error parsing %s" % file_name)
            print(exp)
            exit()
        
        self.dep_track_url = server.TakeAction().create_resource_stack(resource_obj)
        print("Service deployment tracking url:%s" % self.dep_track_url)

        l = self.dep_track_url.rfind("/")
        dep_id = self.dep_track_url[l+1:]
        print("dep id:%s" % dep_id)

        
