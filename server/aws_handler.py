import ast
import base64
import boto3
import json
import os
import shutil
import time
from os.path import expanduser

from common import common_functions
from common import constants
from common import docker_lib
from common import fm_logger
from dbmodule import db_handler
from dbmodule.objects import app as app_db
from dbmodule.objects import environment as env_db
from dbmodule.objects import resource as res_db
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
        self.alb_client = boto3.client('elbv2')
        self.docker_handler = docker_lib.DockerLib()

    @staticmethod
    def get_aws_details():
        region = access_key = secret_key = ''
        aws_creds_path = home_dir + "/.aws"
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
            env_db.Environment().update(env_id, {'status':'creating_' + type})
            status = AWSHandler.registered_resource_handlers[type].create(env_id, resource_details)
            ret_status_list.append(status)
        return ret_status_list

    def delete_resource(self, env_id, resource):
        resource_details = ''
        type = resource[db_handler.RESOURCE_TYPE]
        env_db.Environment().update(env_id, {'status':'deleting_' + type})
        status = AWSHandler.registered_resource_handlers[type].delete(resource)

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

        res_id = res_db.Resource().update_res_for_env(env_id, {'status': 'deleting'})

        cont_name = cluster_name + "-delete"
        err, output = self.docker_handler.build_container_image(cont_name,
                                                                env_store_location + "/Dockerfile.delete-cluster",
                                                                df_context=env_store_location)

        if err:
            fmlogger.debug("Error encountered in building container to delete cluster %s" % cluster_name)
        self.docker_handler.remove_container(cont_name)
        self.docker_handler.remove_container_image(cont_name)
        fmlogger.debug("Done deleting ECS cluster %s" % cluster_name)

        ec2 = boto3.resource('ec2')
        key_pair = ec2.KeyPair(cluster_name)
        try:
            key_pair.delete()
        except Exception as e:
            fmlogger.error("Error encountered in deleting key pair. %s" % e)

        try:
            response = self.ecs_client.delete_cluster(cluster=cluster_name)
        except Exception as e:
            fmlogger.error("Error encountered in deleting cluster %s" % e)

        env_obj = env_db.Environment().get(env_id)
        env_output_config = ast.literal_eval(env_obj.output_config)
        sec_group_name = env_output_config['http-and-ssh-group-name']
        sec_group_id = env_output_config['http-and-ssh-group-id']
        vpc_id = env_output_config['vpc_id']
        AWSHandler.awshelper.delete_security_group_for_vpc(vpc_id, sec_group_id, sec_group_name)

        res_db.Resource().delete(res_id)

    def create_cluster(self, env_id, env_info):
        cluster_status = 'unavailable'
        env_obj = env_db.Environment().get(env_id)
        env_name = env_obj.name

        env_output_config = ast.literal_eval(env_obj.output_config)
        env_version_stamp = env_output_config['env_version_stamp']

        cluster_name = env_name + "-" + env_version_stamp
        keypair_name = cluster_name

        env_store_location = env_info['location']

        if not os.path.exists(env_store_location):
            os.makedirs(env_store_location)
            shutil.copytree(home_dir+"/.aws", env_store_location+"/aws-creds")

        vpc_details = AWSHandler.awshelper.get_vpc_details()
        vpc_id = vpc_details['vpc_id']
        cidr_block = vpc_details['cidr_block']
        subnet_ids = AWSHandler.awshelper.get_subnet_ids(vpc_id)
        subnet_list = ','.join(subnet_ids)

        sec_group_name = cluster_name + "-http-ssh"
        sec_group_id = AWSHandler.awshelper.create_security_group_for_vpc(vpc_id, sec_group_name)

        vpc_traffic_block = []
        internet_traffic = '0.0.0.0/0'
        vpc_traffic_block.append(internet_traffic)
        port_list = [22, 80]
        AWSHandler.awshelper.setup_security_group(vpc_id, vpc_traffic_block,
                                                  sec_group_id, sec_group_name, port_list)

        region, access_key, secret_key = AWSHandler.get_aws_details()

        create_keypair_cmd = ("RUN aws ec2 create-key-pair --key-name "
                              "{key_name} --query 'KeyMaterial' --output text > {key_file}.pem").format(key_name=keypair_name,
                                                                                                        key_file=keypair_name)
        df = self.docker_handler.get_dockerfile_snippet("aws")

        env_details = ast.literal_eval(env_obj.env_definition)
        cluster_size = 1
        if 'cluster_size' in env_details['environment']['app_deployment']:
            cluster_size = env_details['environment']['app_deployment']['cluster_size']
        instance_type = 't2.micro'
        if 'instance_type' in env_details['environment']['app_deployment']:
            instance_type = env_details['environment']['app_deployment']['instance_type']
        entry_point_cmd = ("ENTRYPOINT [\"ecs-cli\", \"up\", \"--size\", \"{size}\", \"--keypair\", \"{keypair}\", \"--capability-iam\", \"--vpc\", \"{vpc_id}\", \"--subnets\", \"{subnet_list}\", "
                           "\"--security-group\", \"{security_group}\", \"--instance-type\", \"{instance_type}\", \"--cluster\", \"{cluster}\"] \n").format(size=cluster_size,
                                                                                                                  cluster=cluster_name, vpc_id=vpc_id,
                                                                                                                  keypair=keypair_name,
                                                                                                                  security_group=sec_group_id,
                                                                                                                  subnet_list=subnet_list,
                                                                                                                  instance_type=instance_type)
        fmlogger.debug("Entry point cmd:%s" % entry_point_cmd)
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "RUN sudo apt-get install -y curl \n"
                   "{create_keypair_cmd} \n"
                   "RUN sudo curl -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-latest \ \n"
                   " && chmod +x /usr/local/bin/ecs-cli \ \n"
                   " && ecs-cli configure --region {reg} --access-key {access_key} --secret-key {secret_key} --cluster {cluster} \n"
                   " {entry_point_cmd}"
                   ).format(create_keypair_cmd=create_keypair_cmd, reg=region, access_key=access_key, secret_key=secret_key,
                            cluster=cluster_name, entry_point_cmd=entry_point_cmd)

        fp = open(env_store_location + "/Dockerfile.create-cluster", "w")
        fp.write(df)
        fp.close()

        res_data = {}
        res_data['env_id'] = env_id
        res_data['cloud_resource_id'] = cluster_name
        res_data['type'] = 'ecs-cluster'
        res_data['status'] = 'provisioning'
        res_id = res_db.Resource().insert(res_data)
        err, image_id = self.docker_handler.build_container_image(cluster_name,
                                                                  env_store_location + "/Dockerfile.create-cluster",
                                                                  df_context=env_store_location)

        err, cont_id = self.docker_handler.run_container(cluster_name)
        cont_id = cont_id.rstrip().lstrip()
        fmlogger.debug("Checking status of ECS cluster %s" % cluster_name)
        is_active = False
        time_out_count = 0
        while not is_active and time_out_count < 300:
            try:
                clusters_dict = self.ecs_client.describe_clusters(clusters=[cluster_name])
                registered_instances_count = clusters_dict['clusters'][0]['registeredContainerInstancesCount']
                if registered_instances_count == cluster_size:
                    is_active = True
                    cluster_status = 'available'
                    break
            except Exception as e:
                fmlogger.debug("Exception encountered in trying to describe clusters:%s" % e)
            time.sleep(2)
            time_out_count = time_out_count + 1

        res_db.Resource().update(res_id, {'status': cluster_status})

        cp_cmd = ("docker cp {cont_id}:/src/{key_file}.pem {env_dir}/.").format(cont_id=cont_id,
                                                                                env_dir=env_store_location,
                                                                                key_file=keypair_name)
        os.system(cp_cmd)


        self.docker_handler.remove_container(cont_id)
        self.docker_handler.remove_container_image(cluster_name)

        env_output_config['subnets'] = subnet_list
        env_output_config['vpc_id'] = vpc_id
        env_output_config['cidr_block'] = cidr_block
        env_output_config['http-and-ssh-group-name'] = sec_group_name
        env_output_config['http-and-ssh-group-id'] = sec_group_id
        env_output_config['key_file'] = env_store_location + "/" + keypair_name + ".pem"

        env_update = {}
        env_update['status'] = env_obj.status
        env_update['output_config'] = str(env_output_config)
        env_db.Environment().update(env_id, env_update)
        fmlogger.debug("Done creating ECS cluster %s" % cluster_name)
        return cluster_status

    def _get_cluster_name(self, env_id):
        resource_obj = res_db.Resource().get_resource_for_env(env_id, 'ecs-cluster')
        cluster_name = resource_obj.cloud_resource_id
        return cluster_name
    
    def _register_task_definition(self, app_info, image, container_port, cont_name=''):
        if not cont_name:
            cont_name = app_info['app_name'] + "-" + app_info['app_version']
        memory = 500 # Default memory size of 500MB. This is hard limit
        if 'memory' in app_info:
            memory = int(app_info['memory'])
        family_name = app_info['app_name']
        task_def_arn = ''
        revision = str(int(round(time.time() * 1000)))
        family_name = family_name + "-" + revision
        try:
            resp = self.ecs_client.register_task_definition(family=family_name,
                                                            containerDefinitions=[{'name': cont_name,
                                                                                   'image': image,
                                                                                   'memory': memory,
                                                                                   'portMappings':[{
                                                                                      'containerPort':container_port,
                                                                                      'hostPort':80,
                                                                                      'protocol':'tcp'}]}])
            task_def_arn = resp['taskDefinition']['taskDefinitionArn']
        except Exception as e:
            fmlogger.debug("Exception encountered in trying to register task definition.")
        fmlogger.debug("Done registering task definition.")
        return task_def_arn, cont_name
    
    def _deregister_task_definition(self, task_def_arn):
        try:
            resp = self.ecs_client.deregister_task_definition(taskDefinition=task_def_arn)
        except Exception as e:
            fmlogger.debug("Exception encountered in deregistering task definition.")

    def _get_app_url(self, app_info, cluster_name):
        app_url = ''
        self._copy_creds(app_info)
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
        app_ip = ''
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
                        app_ip = app_url_str.split("->")[0].strip()
                        app_url = "http://" + app_ip
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

        cluster_name = app_details_obj['cluster_name']
        
        # TODO: When we support multiple instances of a task then
        # we should revisit following logic.
        tasks = self.ecs_client.list_tasks(cluster=cluster_name)
        if 'taskArns' in tasks:
            task_arn = tasks['taskArns'][0] # assuming one task current
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

    def _build_app_container(self, app_info, repo_name, proxy_endpoint, tag=''):
        app_dir = app_info['app_location']
        app_name = app_info['app_name']
        app_version = app_info['app_version']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        cont_name = proxy_endpoint[8:] + "/" + repo_name # Removing initial https:// from proxy_endpoint
        fmlogger.debug("Container name that will be used in building:%s" % cont_name)

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile", 
                                                                df_context=df_dir, tag=tag)
        return err, output, cont_name

    def _copy_creds(self, app_info):
        app_dir = app_info['app_location']
        app_name = app_info['app_name']
        app_version = app_info['app_version']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name

        if not os.path.exists(df_dir + "/aws-creds"):
            shutil.copytree(home_dir +"/.aws", df_dir +"/aws-creds")

    def _update_ecs_app_service(self, app_info, cont_name, task_def_arn, task_desired_count=1):
        cluster_name = self._get_cluster_name(app_info['env_id'])
        service_available = AWSHandler.awshelper.update_service(app_info['app_name'], cluster_name, 
                                                                task_def_arn, task_desired_count)

    def _check_if_app_is_ready(self, app_id, app_ip_url, app_url):
        app_status = ''
        if common_functions.is_app_ready(app_ip_url, app_id=app_id):
            fmlogger.debug("Application is ready.")
            app_status = constants.APP_DEPLOYMENT_COMPLETE + ":" + constants.APP_IP_IS_RESPONSIVE
        else:
            fmlogger.debug("Application could not start properly.")
            app_status = constants.APP_LB_NOT_YET_READY + ":" + constants.USE_APP_IP_URL
        return app_status

    def _create_ecs_app_service(self, app_info, cont_name, task_def_arn):
        app_status = ''
        env_obj = env_db.Environment().get(app_info['env_id'])
        env_output_config = ast.literal_eval(env_obj.output_config)
        subnet_string = env_output_config['subnets']
        subnet_list = subnet_string.split(',')
        sec_group_id = env_output_config['http-and-ssh-group-id']
        vpc_id = env_output_config['vpc_id']
        cluster_name = self._get_cluster_name(app_info['env_id'])
        app_url, lb_arn, target_group_arn, listener_arn = AWSHandler.awshelper.create_service(app_info['app_name'], app_info['app_port'], vpc_id,
                                                                                              subnet_list, sec_group_id, cluster_name,
                                                                                              task_def_arn, cont_name)
        app_ip_url = self._get_app_url(app_info, cluster_name)
        if not app_url:
            app_url = app_ip_url
        else:
            app_url = "http://" + app_url
        fmlogger.debug("App URL:%s" % app_url)
        fmlogger.debug("App IP URL:%s" % app_ip_url)

        return app_url, app_ip_url, lb_arn, target_group_arn, listener_arn

    def _get_container_port(self, task_def_arn):
        container_port = AWSHandler.awshelper.get_container_port_from_taskdef(task_def_arn)
        return container_port

    def redeploy_application(self, app_id, app_info):
        app_location = app_info['app_location']
        self._copy_creds(app_info)

        if app_info['env_id']:
            common_functions.resolve_environment(app_id, app_info)

        app_obj = db_handler.DBHandler().get_app(app_id)
        app_details = app_obj[db_handler.APP_OUTPUT_CONFIG]
        app_details_obj = ast.literal_eval(app_details)
        db_handler.DBHandler().update_app(app_id, 'redeploying', str(app_details_obj))

        memory = ''
        if 'memory' in app_details_obj:
            app_info['memory'] = app_details_obj['memory']
        proxy_endpoint = app_details_obj['proxy_endpoint']
        repo_name = app_details_obj['repo_name']
        tag = str(int(round(time.time() * 1000)))

        db_handler.DBHandler().update_app(app_id, 'building-app-container', str(app_details_obj))
        err, output, image_name = self._build_app_container(app_info, repo_name, proxy_endpoint, tag=tag)
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request.")
            return

        db_handler.DBHandler().update_app(app_id, 'pushing-app-cont-to-ecr-repository', str(app_details_obj))
        tagged_image = image_name + ":" + tag
        err, output = self.docker_handler.push_container(tagged_image)

        common_functions.save_image_tag(tagged_image, app_info)
        if err:
            fmlogger.debug("Error encountered in pushing container image to ECR. Not continuing with the request.")
            db_handler.DBHandler().update_app(app_id, 'error-encountered-in-pushing-app-cont-image', str(app_details_obj))
            raise Exception()
        fmlogger.debug("Completed pushing container %s to AWS ECR" % tagged_image)

        current_task_def_arn = app_details_obj['task_def_arn'][-1]
        container_port = self._get_container_port(current_task_def_arn)
        orig_cont_name = app_details_obj['cont_name']
        db_handler.DBHandler().update_app(app_id, 'deregistering-current-task-ecs-app-service', str(app_details))
        self._update_ecs_app_service(app_info, orig_cont_name, current_task_def_arn, task_desired_count=0)

        db_handler.DBHandler().update_app(app_id, 'registering-new-task-ecs-app-service', str(app_details))
        new_task_def_arn, cont_name = self._register_task_definition(app_info, tagged_image,
                                                                     container_port, cont_name=orig_cont_name)
        self._update_ecs_app_service(app_info, orig_cont_name, new_task_def_arn, task_desired_count=1)

        app_details_obj['task_def_arn'].append(new_task_def_arn)
        app_details_obj['image_name'].append(tagged_image)

        app_ip_url = app_details_obj['app_ip_url']
        app_url = app_details_obj['app_url']
        db_handler.DBHandler().update_app(app_id, 'waiting-for-app-to-get-ready', str(app_details_obj))
        status = self._check_if_app_is_ready(app_id, app_ip_url, app_url)
        db_handler.DBHandler().update_app(app_id, status, str(app_details_obj))

    def deploy_application(self, app_id, app_info):
        app_location = app_info['app_location']
        cloud = app_info['target']
        self._copy_creds(app_info)

        if app_info['env_id']:
            common_functions.resolve_environment(app_id, app_info)

        app_details = {}
        app_data = {}
        app_data['status'] = 'creating-ecr-repository'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)
        repo_name, proxy_endpoint, username, password = self._create_repository(app_info)
        app_details['repo_name'] = repo_name
        app_details['proxy_endpoint'] = proxy_endpoint
        app_details['task-familyName'] = app_info['app_name']

        if username and password and proxy_endpoint:
            err, output = self._set_up_docker_client(username, password, proxy_endpoint)
            if err:
                fmlogger.debug("Error encountered in executing docker login command. Not continuing with the request. %s" % err)
                return

        tag = str(int(round(time.time() * 1000)))

        app_data['status'] = 'building-app-container'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)
        err, output, image_name = self._build_app_container(app_info, repo_name, proxy_endpoint, tag=tag)
        tagged_image = image_name + ":" + tag
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request. %s" % err)
            return

        app_data['status'] = 'pushing-app-cont-to-ecr-repository'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)
        err, output = self.docker_handler.push_container(tagged_image)
        if err:
            fmlogger.debug("Error encountered in pushing container image to ECR. Not continuing with the request.")
            return
        fmlogger.debug("Completed pushing container %s to AWS ECR" % tagged_image)

        app_data['status'] = 'registering-task-definition'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        container_port = int(app_info['app_port'])
        task_def_arn, cont_name = self._register_task_definition(app_info, tagged_image, container_port)
        app_details['task_def_arn'] = [task_def_arn]
        app_details['cont_name'] = cont_name
        app_details['cluster_name'] = self._get_cluster_name(app_info['env_id'])
        app_details['image_name'] = [tagged_image]
        if 'memory' in app_info:
            app_details['memory'] = app_info['memory']

        app_data['status'] = 'creating-ecs-app-service'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        app_url, app_ip_url, lb_arn, target_group_arn, listener_arn = self._create_ecs_app_service(app_info,
                                                                                                   cont_name,
                                                                                                   task_def_arn)
        app_details['lb_arn'] = lb_arn
        app_details['target_group_arn'] = target_group_arn
        app_details['listener_arn'] = listener_arn
        app_details['app_url'] = app_url
        app_details['app_ip_url'] = app_ip_url

        app_data['status'] = 'ecs-app-service-created'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        app_data['status'] = 'waiting-for-app-to-get-ready'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        status = self._check_if_app_is_ready(app_id, app_ip_url, app_url)

        fmlogger.debug('Application URL:%s' % app_url)

        app_data['status'] = status
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting Application:%s" % app_id)
        app_obj = db_handler.DBHandler().get_app(app_id)
        app_details = app_obj[db_handler.APP_OUTPUT_CONFIG]
        app_details_obj = ast.literal_eval(app_details)
        app_details_obj['app_url'] = ''
        status = 'deleting'
        db_handler.DBHandler().update_app(app_id, status, str(app_details_obj))

        task_def_arn_list = app_details_obj['task_def_arn']

        latest_task_def_arn = task_def_arn_list[-1]
        cont_name = app_details_obj['cont_name']
        self._update_ecs_app_service(app_info, cont_name, latest_task_def_arn, task_desired_count=0)

        for task_def_arn in task_def_arn_list:
            self._deregister_task_definition(task_def_arn)

        self.ecs_client.delete_service(cluster=app_details_obj['cluster_name'],
                                       service=app_obj[db_handler.APP_NAME])

        try:
            self.alb_client.delete_listener(ListenerArn=app_details_obj['listener_arn'])
        except Exception as e:
            fmlogger.error("Exception encountered in deleting listener %s" % e)

        try:
            self.alb_client.delete_target_group(TargetGroupArn=app_details_obj['target_group_arn'])
        except Exception as e:
            fmlogger.error("Exception encountered in deleting target group %s" % e)

        try:
            self.alb_client.delete_load_balancer(LoadBalancerArn=app_details_obj['lb_arn'])
        except Exception as e:
            fmlogger.error("Exception encountered in deleting load balancer %s" % e)

        self._delete_repository(app_obj[db_handler.APP_NAME])

        #tagged_image_list = common_functions.read_image_tag(app_info)
        tagged_image_list = app_details_obj['image_name']
        if tagged_image_list:
            for tagged_image in tagged_image_list:
                self.docker_handler.remove_container_image(tagged_image)

        #image_name = app_details_obj['image_name']
        #self.docker_handler.remove_container_image(image_name + ":latest")

        db_handler.DBHandler().delete_app(app_id)
