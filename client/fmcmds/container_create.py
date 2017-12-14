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
                            help="Type of repository for storing the container. Supported options: 'ecr', 'gcr', 'local'.")

        parser.add_argument('--project-id',
                            dest='project_id',
                            help="Project ID (Required when repository type is 'gcr')")
        return parser

    def take_action(self, parsed_args):
        cont_info = {}
        cont_name = parsed_args.container_name
        cont_info['cont_name'] = cont_name

        repository = parsed_args.repository.strip()
        cont_info['dep_target'] = repository

        if repository != 'gcr' and repository != 'ecr' and repository != 'local':
            print("Incorrect repository destination specified. Should be one of: ecr, gcr, local")
            exit()

        if repository == 'gcr':
            if not common.cloud_setup('gcloud'):
                print("Cloud setup not done for Google cloud. Please run 'cld setup gcloud' and then ./<cloudark-dir>/restart-cloudark.sh")
                exit()
            project_id = ''
            if not parsed_args.project_id:
                project_id = raw_input("Project ID>")
            else:
                project_id = parsed_args.project_id

            cont_info['project'] = project_id

        if repository == 'ecr':
            if not common.cloud_setup('aws'):
                print("Cloud setup not done for AWS cloud. Please run 'cld setup aws' and then ./<cloudark-dir>/restart-cloudark.sh")
                exit()

        cont_df_location = os.getcwd()
        if not os.path.exists(cont_df_location + "/Dockerfile"):
            print("There is no Dockerfile in this directory. Exiting.")
            exit()
        cont_df_folder_name = common.get_app_folder_name(cont_df_location)
        cont_info['cont_df_folder_name'] = cont_df_folder_name

        source_dir = os.getcwd()
        server.TakeAction().create_container(source_dir, cont_info)
