import os
from os.path import expanduser
import yaml

from cliff.command import Command
import common
from pydoc import locate

import call_server as server

env_file_request_string = "YAML file containing environment resource specification"

not_allowed_regex_list = ["--+", "^\d", "-$"]

import subprocess

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)


class EnvironmentCreate(Command):

    def get_parser(self, prog_name):
        parser = super(EnvironmentCreate, self).get_parser(prog_name)

        parser.add_argument(dest='env_name',
                            help="Name that you want to give to the environment")

        parser.add_argument(dest='file_name',
                            help=env_file_request_string)

        parser.add_argument('--project-id',
                            dest='project_id',
                            help="Project ID (Required when environment definition contains Google-based platform elements)")
        return parser

    # Template of how to load plugins -- Currently not required
    def _load_plugins(self):
        plugin_list = []
        fp = open("/etc/firstmile/firstmile-client.conf", "r")
        lines = fp.readlines()
        for line in lines:
            if line.find("clients=") >= 0:
                pluginList = line.split("=")
                plugin_list = pluginList[1].split(",")

        print("Plugin list:%s" % plugin_list)
        for plugin in plugin_list:
            plugin_class = locate(plugin)
            plugin_class.verify_cli_options()

    def take_action(self, parsed_args):

        env_name = parsed_args.env_name

        is_name_invalid = common.check_env_name(env_name,
                                                not_allowed_regex_list)

        if is_name_invalid or len(env_name) > 10:
            print("Invalid environment name. Please follow these constraints for env name:")
            print("- Must be upto 10 characters in length.")
            print("- May contain alphanumeric characters or hyphens.")
            print("- First character must be a letter.")
            print("- Cannot end with a hyphen or contain two consecutive hyphens.")
            exit(0)

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
            # TODO(devdatta): Verify that each resource definition contains the 'type' attribute
        except Exception as exp:
            print("Error parsing %s" % file_name)
            print(exp)
            exit()

        cloud_list = common.parse_clouds(environment_def)

        setup_not_done = False
        for cloud in cloud_list:
            if not common.cloud_setup(cloud):
                setup_not_done = True
                print("Setup not done for cloud %s. Run 'cld setup %s' to do the setup." % (cloud, cloud))
                print("Once setup is done, restart cloudark server: ./<cloudark-dir>/restart-cloudark.sh")

        if setup_not_done:
            exit()

        if 'app_deployment' not in environment_def['environment']:
            print("app_deployment attribute missing from environment definition.")
            exit()
        if environment_def['environment']['app_deployment']['target'] == 'gcloud':
            project_id = ''
            if not parsed_args.project_id:
                project_id = raw_input("Project ID>")
            else:
                project_id = parsed_args.project_id
            environment_def['environment']['app_deployment']['project'] = project_id.strip()

            zone = ''
            cloudark_google_setup_details_path = APP_STORE_PATH + "/google-creds-cloudark"
            fp = open(cloudark_google_setup_details_path, "r")
            line = fp.readline()
            parts = line.split(":")
            zone = parts[1]

            environment_def['environment']['app_deployment']['project'] = project_id
            environment_def['environment']['app_deployment']['zone'] = zone

        server.TakeAction().create_environment(env_name, environment_def)
