import ast
import base64
import boto3
import json
import os
import shutil
import time

from common import common_functions
from common import constants
from common import fm_logger
from dbmodule import db_handler
from common import docker_lib

from os.path import expanduser

from server.server_plugins.aws import aws_helper
from server.server_plugins.aws.resource import rds_handler
from server.server_plugins.aws.resource import dynamodb_handler

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()
dbhandler = db_handler.DBHandler()

class AWSHandler(object):

    registered_resource_handlers = dict()
    registered_resource_handlers['rds'] = rds_handler.RDSResourceHandler()
    registered_resource_handlers['dynamodb'] = dynamodb_handler.DynamoDBResourceHandler()
    awshelper = aws_helper.AWSHelper()
    
    def __init__(self):
        self.ecr_client = boto3.client('ecr')
        self.ecs_client = boto3.client('ecs')
        self.docker_handler = docker_lib.DockerLib()

    @staticmethod
    def get_aws_details():
        region = access_key = secret_key = ''
        aws_creds_path = APP_AND_ENV_STORE_PATH + "/aws-creds"
        creds_file_path = aws_creds_path + "/credentials"
        config_file_path = aws_creds_path + "/config"
        incorrect_setup = False
        if not os.path.exists(creds_file_path) or \
            not os.path.exists(config_file_path):
            incorrect_setup = True
        else:
            fp = open(aws_creds_path + "/credentials", "r")
            lines = fp.readlines()
            for line in lines:
                line = line.rstrip()
                if line.find("aws_access_key_id") >= 0:
                    parts = line.split("=")
                    if parts[1] == '':
                        incorrect_setup = True
                    else:
                        access_key = parts[1].lstrip().rstrip()
                if line.find("aws_secret_access_key") >= 0:
                    parts = line.split("=")
                    if parts[1] == '':
                        incorrect_setup = True
                    else:
                        secret_key = parts[1].lstrip().rstrip()
            fp = open(aws_creds_path + "/config", "r")
            lines = fp.readlines()
            for line in lines:
                line = line.rstrip()
                if line.find("output") >= 0:
                    parts = line.split("=")
                    if parts[1] == '':
                        incorrect_setup = True
                if line.find("region") >= 0:
                    parts = line.split("=")
                    if parts[1] == '':
                        incorrect_setup = True
                    else:
                        region = parts[1].lstrip().rstrip()        
        if incorrect_setup:
            raise RuntimeError('AWS creds not setup properly.')

        return region, access_key, secret_key

    def create_resources(self, env_id, resource_list):
        resource_details = ''
        ret_status_list = []
        for resource_defs in resource_list:
            resource_details = resource_defs['resource']
            type = resource_details['type']
            status = AWSHandler.registered_resource_handlers[type].create(env_id, resource_details)
            ret_status_list.append(status)
        return ret_status_list

    def delete_cluster(self, env_id, env_info, resource):
        cluster_name = resource[db_handler.RESOURCE_NAME]

        df = self.docker_handler.get_dockerfile_snippet("aws")
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "RUN sudo apt-get install -y curl \n"
                   "RUN sudo curl -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-latest \ \n"
                   " && chmod +x /usr/local/bin/ecs-cli \ \n"
                   " && ecs-cli down --cluster {cluster} --force").format(cluster=cluster_name)

        env_store_location = env_info['location']

        fp = open(env_store_location + "/Dockerfile.delete-cluster", "w")
        fp.write(df)
        fp.close()

        res_id = db_handler.DBHandler().update_resource_for_environment(env_id, 'deleting')
        
        cont_name = cluster_name + "-delete"
        err, output = self.docker_handler.build_container_image(cont_name,
                                                                env_store_location + "/Dockerfile.delete-cluster",
                                                                df_context=env_store_location)

        if err:
            fmlogger.debug("Error encountered in building container to delete cluster %s" % cluster_name)
        self.docker_handler.remove_container(cont_name)
        self.docker_handler.remove_container_image(cont_name)
        fmlogger.debug("Done deleting ECS cluster %s" % cluster_name)
        db_handler.DBHandler().delete_resource(res_id)

    def create_cluster(self, env_id, env_info):
        ret_status = 'unavailable'
        env_obj = dbhandler.get_environment(env_id)
        env_name = env_obj[db_handler.ENV_NAME]

        env_output_config = ast.literal_eval(env_obj[db_handler.ENV_OUTPUT_CONFIG])
        env_version_stamp = env_output_config['env_version_stamp']
        
        cluster_name = env_name + "-" + env_version_stamp
        keypair_name = cluster_name

        env_store_location = env_info['location']
        
        if not os.path.exists(env_store_location):
            os.makedirs(env_store_location)
            shutil.copytree(APP_AND_ENV_STORE_PATH+"/aws-creds", env_store_location+"/aws-creds")

        vpc_details = AWSHandler.awshelper.get_vpc_details()
        vpc_id = vpc_details['vpc_id']
        cidr_block = vpc_details['cidr_block']
        subnet_ids = AWSHandler.awshelper.get_subnet_ids(vpc_id)
        subnet_list = ','.join(subnet_ids)

        sec_group_name = cluster_name + "-http-ssh"
        sec_group_id = AWSHandler.awshelper.create_security_group_for_vpc(vpc_id, sec_group_name)

        internet_traffic = '0.0.0.0/0'
        port_list = [22, 80]
        AWSHandler.awshelper.setup_security_group(vpc_id, internet_traffic,
                                                  sec_group_id, sec_group_name, port_list)

        region, access_key, secret_key = AWSHandler.get_aws_details()

        create_keypair_cmd = ("RUN aws ec2 create-key-pair --key-name "
                              "{key_name} --query 'KeyMaterial' --output text > {key_file}.pem").format(key_name=keypair_name,
                                                                                                        key_file=keypair_name)
        df = self.docker_handler.get_dockerfile_snippet("aws")
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "RUN sudo apt-get install -y curl \n"
                   "{create_keypair_cmd} \n"
                   "RUN sudo curl -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-latest \ \n"
                   " && chmod +x /usr/local/bin/ecs-cli \ \n"
                   " && ecs-cli configure --region {reg} --access-key {access_key} --secret-key {secret_key} --cluster {cluster} \ \n"
                   " && ecs-cli up --keypair {keypair} --capability-iam --vpc {vpc_id} --subnets {subnet_list} --security-group {security_group} --cluster {cluster}"
                   ).format(create_keypair_cmd=create_keypair_cmd, reg=region, access_key=access_key, secret_key=secret_key,
                            cluster=cluster_name, vpc_id=vpc_id, security_group=sec_group_id, subnet_list=subnet_list, keypair=keypair_name)

        fp = open(env_store_location + "/Dockerfile.create-cluster", "w")
        fp.write(df)
        fp.close()

        res_id = db_handler.DBHandler().add_resource(env_id, cluster_name, 'ecs-cluster', 'provisioning')
        err, output = self.docker_handler.build_container_image(cluster_name,
                                                                env_store_location + "/Dockerfile.create-cluster",
                                                                df_context=env_store_location)

        fmlogger.debug("Checking status of ECS cluster %s" % cluster_name)
        is_active = False
        issue_encountered = False
        while not is_active and not issue_encountered:
            try:
                clusters_dict = self.ecs_client.describe_clusters(clusters=[cluster_name])
                status = clusters_dict['clusters'][0]['status']
                if status == 'ACTIVE':
                    is_active = True
                    ret_status = 'available'
                    break
            except Exception as e:
                fmlogger.debug("Exception encountered in trying to describe clusters:%s" % e)
                issue_encountered = True

        db_handler.DBHandler().update_resource(res_id, status='available')

        self.docker_handler.remove_container(cluster_name)
        self.docker_handler.remove_container_image(cluster_name)

        env_output_config['subnets'] = subnet_list
        env_output_config['vpc_id'] = vpc_id
        env_output_config['cidr_block'] = cidr_block
        env_output_config['http-and-ssh-group-name'] = sec_group_name
        env_output_config['http-and-ssh-group-id'] = sec_group_id
        db_handler.DBHandler().update_environment(env_id, status=env_obj[db_handler.ENV_STATUS],
                                                  output_config=str(env_output_config))
        fmlogger.debug("Done creating ECS cluster %s" % cluster_name)
        return ret_status

    def create_cluster_bak(self, env_id, app_info):
        env_name = dbhandler.get_environment(env_id)
        cluster_name = env_name + "-" + env_id
        #if 'env_id' in app_info:
        #    cluster_name = cluster_name + "-" + app_info['env_id']
        try:
            clusters_dict = self.ecs_client.describe_clusters(clusters=[cluster_name])
            if len(clusters_dict['failures']) >= 1:
                failure_reason = clusters_dict['failures'][0]['reason']
                if failure_reason == 'MISSING':
                    try:
                        cluster_creation_response = self.ecs_client.create_cluster(clusterName=cluster_name)
                    except Exception as e1:
                        fmlogger.debug("Exception encountered in trying to create cluster:%s. Returning" % e1)
                        return
        except Exception as e:
            fmlogger.debug("Exception encountered in trying to describe clusters:%s" % e)
        
    
    def _get_cluster_name(self, env_id):
        resource_obj = db_handler.DBHandler().get_resources_for_environment(env_id)
        cluster_name = resource_obj[0][db_handler.RESOURCE_NAME]
        return cluster_name
    
    def _register_task_definition(self, app_info, image):
        cont_name = app_info['app_name'] + "-" + app_info['app_version']
        family_name = app_info['app_name']
        task_def_arn = ''
        try:
            resp = self.ecs_client.register_task_definition(family=family_name,
                                                            containerDefinitions=[{'name': cont_name,
                                                                                   'image': image,
                                                                                   'memory': 500, # Default memory size of 500MB. This is hard limit
                                                                                   'portMappings':[{
                                                                                      'containerPort':int(app_info['app_port']),
                                                                                      'hostPort':80,
                                                                                      'protocol':'tcp'}]}])
            task_def_arn = resp['taskDefinition']['taskDefinitionArn']
        except Exception as e:
            fmlogger.debug("Exception encountered in trying to register task definition.")
        fmlogger.debug("Done registering task definition.")
        return task_def_arn,cont_name
    
    def _deregister_task_definition(self, task_def_arn):
        try:
            resp = self.ecs_client.deregister_task_definition(taskDefinition=task_def_arn)
        except Exception as e:
            fmlogger.debug("Exception encountered in deregistering task definition.")

    def _get_app_url(self, app_info, cluster_name):
        app_url = ''
        df = self.docker_handler.get_dockerfile_snippet("aws")
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "RUN sudo apt-get install -y curl \n"
                   "RUN sudo curl -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-latest \ \n"
                   " && chmod +x /usr/local/bin/ecs-cli \n"
                   "ENTRYPOINT [\"ecs-cli\", \"ps\", \"--cluster\", \"{cluster_name}\"]").format(cluster_name=cluster_name)

        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        cont_name = app_info['app_name'] + "-get-cont-ip"

        df_dir = app_dir + "/" + app_folder_name
        fp = open(df_dir+"/Dockerfile.get-cont-ip", "w")
        fp.write(df)
        fp.close()

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile.get-cont-ip", 
                                                                df_context=df_dir)

        if not err:
            run_err, run_output = self.docker_handler.run_container_sync(cont_name)
        
            task_name = app_info['app_name']
            lines = run_output.split("\n")
            for line in lines:
                str1 = ' '.join(line.split())
                parts = str1.split(" ")
                if parts[3].strip().find(task_name) >= 0:
                    if parts[1].strip() == 'RUNNING':
                        app_url_str = parts[2].strip()
                        app_url = app_url_str.split("->")[0].strip()
                        break
            self.docker_handler.stop_container(cont_name)
            self.docker_handler.remove_container(cont_name)
            self.docker_handler.remove_container_image(cont_name)
        fmlogger.debug("App URL:%s" % app_url)
        return app_url
    
    def _check_task(self, cluster_name, task_arn, status):
        status_reached = False
        issue_encountered = False
        task_desc = ''
        while not status_reached and not issue_encountered:
            try:
                task_desc = self.ecs_client.describe_tasks(cluster=cluster_name,
                                                           tasks=[task_arn])
                cont_status = task_desc['tasks'][0]['containers'][0]['lastStatus']
                if cont_status.lower() == status:
                    status_reached = True
            except Exception as e:
                fmlogger.debug("Exception encountered in trying to run describe_tasks.")
                issue_encountered = True
        return task_desc
    
    def _stop_task(self, app_id):
        app_obj = db_handler.DBHandler().get_app(app_id)
        app_details = app_obj[db_handler.APP_OUTPUT_CONFIG]
        app_details_obj = ast.literal_eval(app_details)
        
        task_arn = app_details_obj['task_arn']
        cluster_name = app_details_obj['cluster_name']
        try:
            resp = self.ecs_client.stop_task(cluster=cluster_name, task=task_arn)
        except Exception as e:
            fmlogger.debug("Exception encountered in trying to stop_task")
        
        task_desc = self._check_task(cluster_name, task_arn, 'stopped')
        
        fmlogger.debug("Task stopped:%s" % task_arn)
    
    def _run_task(self, app_info):
        family_name = app_info['app_name']
        env_id = app_info['env_id']
        cluster_name = self._get_cluster_name(env_id)
        task_arn = ''
        try:
            resp = self.ecs_client.run_task(cluster=cluster_name, taskDefinition=family_name)
            task_arn = resp['tasks'][0]['taskArn']
        except Exception as e:
            fmlogger.debug("Exception encountered in trying to run_task")

        task_desc = self._check_task(cluster_name, task_arn, 'running')

        container_ip = task_desc['tasks'][0]['containers'][0]['networkBindings'][0]['bindIP']
        host_port = task_desc['tasks'][0]['containers'][0]['networkBindings'][0]['hostPort']
        application_url1 = container_ip + ":" + str(host_port)
        application_url = self._get_app_url(app_info, cluster_name)
        fmlogger.debug("Completed Running task")

        return application_url, task_arn, cluster_name

    def _delete_repository(self, repo_name):
        try:
            resp = self.ecr_client.delete_repository(repositoryName=repo_name, force=True)
        except Exception as e:
            fmlogger.debug("Exception encountered in trying to delete repository:%s" % e)

    def _create_repository(self, app_info):
        proxy_endpoint = ''
        username = ''
        password = ''
        repo_name = app_info['app_name']
        try:
            repo_dict = self.ecr_client.describe_repositories(repositoryNames=[repo_name])
        except Exception as e:
            fmlogger.debug("Exception encountered in trying to describe repositories:%s" % e)
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

    def _build_app_container(self, app_info, repo_name, proxy_endpoint):
        app_dir = app_info['app_location']
        app_name = app_info['app_name']
        app_version = app_info['app_version']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        cont_name = proxy_endpoint[8:] + "/" + repo_name # Removing initial https:// from proxy_endpoint
        fmlogger.debug("Container name that will be used in building:%s" % cont_name)

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile", 
                                                                df_context=df_dir)
        return err, output, cont_name
    
    def deploy_application_1(self, app_id, app_info):
        cont_name = '007068346857.dkr.ecr.us-west-2.amazonaws.com/hello-aws-2'
        app_url = self._run_task(app_info)
        fmlogger.debug('Application URL:%s' % app_url)

    def _copy_creds(self, app_info):
        app_dir = app_info['app_location']
        app_name = app_info['app_name']
        app_version = app_info['app_version']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        shutil.copytree(APP_AND_ENV_STORE_PATH+"/aws-creds", df_dir +"/aws-creds")

    def _create_ecs_app_service(self, app_info, cont_name, task_def_arn):
        env_obj = db_handler.DBHandler().get_environment(app_info['env_id'])
        env_output_config = ast.literal_eval(env_obj[db_handler.ENV_OUTPUT_CONFIG])
        subnet_string = env_output_config['subnets']
        subnet_list = subnet_string.split(',')
        sec_group_id = env_output_config['http-and-ssh-group-id']
        vpc_id = env_output_config['vpc_id']
        cluster_name = self._get_cluster_name(app_info['env_id'])
        app_url = AWSHandler.awshelper.create_service(app_info['app_name'], app_info['app_port'], vpc_id, 
                                                      subnet_list, sec_group_id, cluster_name,
                                                      task_def_arn, cont_name)
        fmlogger.debug("App URL:%s" % app_url)
        return app_url, cluster_name

    def redeploy_application(self, app_id, app_info):
        app_location = app_info['app_location']
        cloud = app_info['target']
        self._copy_creds(app_info)

        if app_info['env_id']:
            common_functions.resolve_environment(app_id, app_info)

        app_obj = db_handler.DBHandler().get_app(app_id)
        app_details = app_obj[db_handler.APP_OUTPUT_CONFIG]
        app_details_obj = ast.literal_eval(app_details)
        app_details_obj['app_url'] = ''
        status = 'redeploying'
        db_handler.DBHandler().update_app(app_id, status, str(app_details_obj))
        
        proxy_endpoint = app_details_obj['proxy_endpoint']
        repo_name = app_details_obj['repo_name']

        db_handler.DBHandler().update_app(app_id, 'building-app-container', str(app_details_obj))
        err, output, cont_name = self._build_app_container(app_info, repo_name, proxy_endpoint)
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request.")
            return

        db_handler.DBHandler().update_app(app_id, 'pushing-app-cont-to-ecr-repository', str(app_details_obj))
        err, output = self.docker_handler.push_container(cont_name)
        if err:
            fmlogger.debug("Error encountered in pushing container image to ECR. Not continuing with the request.")
            return
        # We could remove the container image here; but it delays future pushes as then we have
        # to pay penalty of building the image first and then pushing it to ECR. Another advantage of not
        # deleting image is that subsequent builds are faster due to existing image layers.
        # So we should delete the image only when application is deleted.
        #else:
            #fmlogger.debug("Done pushing container image to ECR. Removing the local image.")
            #self.docker_handler.remove_container_image(cont_name)
        fmlogger.debug("Completed pushing container %s to AWS ECR" % cont_name)

        db_handler.DBHandler().update_app(app_id, 'stopping-previous-task', str(app_details_obj))
        self._stop_task(app_id)

        db_handler.DBHandler().update_app(app_id, 'running-task', str(app_details_obj))
        app_url, task_arn, cluster_name = self._run_task(app_info)
        fmlogger.debug('Application URL:%s' % app_url)

        app_details_obj['app_url'] = app_url
        app_details_obj['task_arn'] = task_arn
        app_details_obj['cluster_name'] = cluster_name
        app_details_obj['cont_name'] = cont_name
        db_handler.DBHandler().update_app(app_id, 'available', str(app_details_obj))

    def deploy_application(self, app_id, app_info):
        app_location = app_info['app_location']
        cloud = app_info['target']
        self._copy_creds(app_info)

        if app_info['env_id']:
            common_functions.resolve_environment(app_id, app_info)
        
        app_details = {}
        db_handler.DBHandler().update_app(app_id, 'creating-ecr-repository', str(app_details))
        repo_name, proxy_endpoint, username, password = self._create_repository(app_info)
        app_details['repo_name'] = repo_name
        app_details['proxy_endpoint'] = proxy_endpoint
        app_details['task-familyName'] = app_info['app_name']

        if username and password and proxy_endpoint:
            err, output = self._set_up_docker_client(username, password, proxy_endpoint)
            if err:
                fmlogger.debug("Error encountered in executing docker login command. Not continuing with the request. %s" % err)
                return

        db_handler.DBHandler().update_app(app_id, 'building-app-container', str(app_details))
        err, output, image_name = self._build_app_container(app_info, repo_name, proxy_endpoint)
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request. %s" % err)
            return

        db_handler.DBHandler().update_app(app_id, 'pushing-app-cont-to-ecr-repository', str(app_details))
        err, output = self.docker_handler.push_container(image_name)
        if err:
            fmlogger.debug("Error encountered in pushing container image to ECR. Not continuing with the request.")
            return
        #else:
        #    fmlogger.debug("Done pushing container image to ECR. Removing the local image.")
        #    self.docker_handler.remove_container_image(image_name)
        fmlogger.debug("Completed pushing container %s to AWS ECR" % image_name)

        db_handler.DBHandler().update_app(app_id, 'registering-task-definition', str(app_details))
        task_def_arn, cont_name = self._register_task_definition(app_info, image_name)

        db_handler.DBHandler().update_app(app_id, 'creating-ecs-app-service', str(app_details))
        app_url, cluster_name = self._create_ecs_app_service(app_info, cont_name, task_def_arn)

        #db_handler.DBHandler().update_app(app_id, 'running-task', str(app_details))
        #app_url, task_arn, cluster_name = self._run_task(app_info)
        fmlogger.debug('Application URL:%s' % app_url)

        app_details['task_def_arn'] = task_def_arn
        app_details['app_url'] = app_url
        #app_details['task_arn'] = task_arn
        app_details['cluster_name'] = cluster_name
        app_details['image_name'] = image_name
        app_details['cont_name'] = cont_name
        db_handler.DBHandler().update_app(app_id, 'available', str(app_details))

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting Application:%s" % app_id)
        app_obj = db_handler.DBHandler().get_app(app_id)
        app_details = app_obj[db_handler.APP_OUTPUT_CONFIG]
        app_details_obj = ast.literal_eval(app_details)
        app_details_obj['app_url'] = ''
        status = 'deleting'
        db_handler.DBHandler().update_app(app_id, status, str(app_details_obj))

        self._stop_task(app_id)
        
        cont_name = app_details_obj['cont_name']
        self.docker_handler.remove_container_image(cont_name)
        
        repo_name = app_obj[db_handler.APP_NAME]
        self._delete_repository(repo_name)
        
        task_def_arn = app_details_obj['task_def_arn']
        self._deregister_task_definition(task_def_arn)
        
        db_handler.DBHandler().delete_app(app_id)
