import ast
import base64
import boto3
import os
from os.path import expanduser
import shutil
import time

import server.server_plugins.resource_base as resource_base
from server.common import constants
from server.common import common_functions
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import container as cont_db
from server.server_plugins.aws import aws_helper

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()


class ECRHandler(resource_base.ResourceBase):
    """ECR Resource handler."""

    awshelper = aws_helper.AWSHelper()

    def __init__(self):
        self.ecr_client = boto3.client('ecr')
        self.docker_handler = docker_lib.DockerLib()

    def _create_repository(self, cont_info):
        proxy_endpoint = ''
        username = ''
        password = ''
        repo_name = cont_info['cont_name']
        try:
            self.ecr_client.describe_repositories(repositoryNames=[repo_name])
        except Exception as e:
            fmlogger.error("Exception encountered in trying to describe repositories:%s" % e)
            create_repo_response = self.ecr_client.create_repository(repositoryName=repo_name)
            repository_dict = create_repo_response['repository']
            registryId = repository_dict['registryId']
            token_response = self.ecr_client.get_authorization_token(registryIds=[registryId])
            auth_token = token_response['authorizationData'][0]['authorizationToken']
            decoded_auth_token = base64.b64decode(auth_token)
            parts = decoded_auth_token.split(":")
            username = parts[0]
            password = parts[1]
            proxy_endpoint = token_response['authorizationData'][0]['proxyEndpoint']
            fmlogger.debug("Done creating repository.")
        return repo_name, proxy_endpoint, username, password

    def _set_up_docker_client(self, username, password, proxy_endpoint):
        err, output = self.docker_handler.docker_login(username, password, proxy_endpoint)
        return err, output

    def _build_container(self, cont_info, repo_name, proxy_endpoint, tag=''):
        df_dir = common_functions.get_df_dir(cont_info)
        cont_name = proxy_endpoint[8:] + "/" + repo_name  # Removing initial https:// from proxy_endpoint
        fmlogger.debug("Container name that will be used in building:%s" % cont_name)

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile",
                                                                df_context=df_dir, tag=tag)
        return err, output, cont_name

    def _delete_repository(self, repo_name):
        try:
            self.ecr_client.delete_repository(repositoryName=repo_name, force=True)
        except Exception as e:
            fmlogger.error("Exception encountered in trying to delete repository:%s" % e)

    def create(self, cont_name, cont_info):

        df_dir = common_functions.get_df_dir(cont_info)
        if not os.path.exists(df_dir + "/aws-creds"):
            shutil.copytree(home_dir + "/.aws", df_dir + "/aws-creds")

        cont_details = {}
        cont_data = {}

        cont_db.Container().update(cont_name, cont_data)

        cont_data['status'] = 'creating-ecr-repository'
        cont_data['output_config'] = str(cont_details)
        cont_db.Container().update(cont_name, cont_data)
        repo_name, proxy_endpoint, username, password = self._create_repository(cont_info)
        cont_details['repo_name'] = repo_name
        cont_details['proxy_endpoint'] = proxy_endpoint

        if username and password and proxy_endpoint:
            err, output = self._set_up_docker_client(username, password, proxy_endpoint)
            if err and err.strip() != 'WARNING! Using --password via the CLI is insecure. Use --password-stdin.':
                fmlogger.debug("Error encountered in executing docker login command. Not continuing with the request. %s" % err)
                return

        tag = str(int(round(time.time() * 1000)))

        cont_data['status'] = 'building-container'
        cont_data['output_config'] = str(cont_details)
        cont_db.Container().update(cont_name, cont_data)
        err, output, image_name = self._build_container(cont_info, repo_name, proxy_endpoint, tag=tag)
        tagged_image = image_name + ":" + tag
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request. %s" % err)
            return

        cont_details = {'tagged_image': tagged_image}
        cont_data['status'] = 'pushing-app-cont-to-ecr-repository'
        cont_data['output_config'] = str(cont_details)
        cont_db.Container().update(cont_name, cont_data)
        err, output = self.docker_handler.push_container(tagged_image)
        if err:
            fmlogger.debug("Error encountered in pushing container image to ECR. Not continuing with the request.")
            return
        fmlogger.debug("Completed pushing container %s to AWS ECR" % tagged_image)

        cont_data['status'] = 'container-ready'
        cont_db.Container().update(cont_name, cont_data)

    def delete(self, cont_name, cont_info):
        try:
            self._delete_repository(cont_name)
        except Exception as e:
            fmlogger.error("Exception encountered while deleting ecr repository %s" % e)
