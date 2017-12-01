import os

from cliff.command import Command

import call_server as server
import common


class ContainerCreate(Command):

    def _read_dockerfile(self):
        if not os.path.exists("Dockerfile"):
            print("Dockerfile not present. Exiting.")
            exit()
        fp = open("Dockerfile", "r")
        content = fp.readlines()
        return content

    def get_parser(self, prog_name):
        parser = super(ContainerCreate, self).get_parser(prog_name)

        parser.add_argument('container_name',
                            help="Container name")

        parser.add_argument('repository',
                            help="Name of repository to push container to. Supported options: 'ecr', 'gcr', 'local'.")

        parser.add_argument('--project-id',
                            dest='project_id',
                            help="Project ID (Required only when repository = gcr")
        return parser

    def take_action(self, parsed_args):
        cont_info = {}
        cont_name = parsed_args.container_name
        cont_info['cont_name'] = cont_name

        repository = parsed_args.repository
        cont_info['dep_target'] = repository
        
        if repository == 'gcr':
            if not parsed_args.project_id:
                print("Project ID not specified.")
                exit()
            else:
                cont_info['project'] = parsed_args.project_id

        cont_df_location = os.getcwd()
        cont_df_folder_name = common.get_app_folder_name(cont_df_location)
        cont_info['cont_df_folder_name'] = cont_df_folder_name

        source_dir = os.getcwd()
        server.TakeAction().create_container(source_dir, cont_info)
