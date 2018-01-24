import ast
import base64
import boto3
import json
import os
from os.path import expanduser
import re
import shutil
import time

import server.server_plugins.coe_base as coe_base
from server.common import common_functions
from server.common import constants
from server.common import docker_lib
from server.common import exceptions
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
from server.server_plugins.aws import aws_helper

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()


class ECSHandler(coe_base.COEBase):
    """ECS Handler."""

    awshelper = aws_helper.AWSHelper()

    allowed_commands = ["aws ecs delete-cluster*",
                        "aws ecs delete-service*",
                        "aws ecs describe-clusters*",
                        "aws ecs describe-container-instances*",
                        "aws ecs describe-services*",
                        "aws ecs describe-task-definition*",
                        "aws ecs describe-tasks*",
                        "aws ecs list-clusters*",
                        "aws ecs list-container-instances*",
                        "aws ecs list-services*",
                        "aws ecs list-taks-definition-families*",
                        "aws ecs list-task-definitions*",
                        "aws ecs list-tasks*",
                        ]

    help_commands = ["aws ecs delete-cluster",
                     "aws ecs delete-service",
                     "aws ecs describe-clusters",
                     "aws ecs describe-container-instances",
                     "aws ecs describe-services",
                     "aws ecs describe-task-definition",
                     "aws ecs describe-tasks",
                     "aws ecs list-clusters",
                     "aws ecs list-container-instances",
                     "aws ecs list-services",
                     "aws ecs list-taks-definition-families",
                     "aws ecs list-task-definitions",
                     "aws ecs list-tasks",
                    ]

    def __init__(self):
        self.ecs_client = boto3.client('ecs')
        self.alb_client = boto3.client('elbv2')
        self.docker_handler = docker_lib.DockerLib()

    def _verify(self, command):
        matched = None
        for pattern in ECSHandler.allowed_commands:
            p = re.compile(pattern, re.IGNORECASE)
            matched = p.match(command)
            if matched:
                return True
        return False

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

    def _get_cluster_name(self, env_id):
        resource_obj = res_db.Resource().get_resource_for_env_by_type(env_id, 'ecs-cluster')
        cluster_name = resource_obj.cloud_resource_id
        return cluster_name

    def _register_task_definition(self, app_info, image, container_port, host_port, env_vars_dict, cont_name=''):
        if not cont_name:
            cont_name = app_info['app_name'] + "-" + app_info['app_version']
        memory = 250  # Default memory size of 250MB. This is hard limit
        mem1 = common_functions.get_app_memory(app_info)
        if mem1:
            memory = int(mem1)

        family_name = app_info['app_name']
        task_def_arn = ''
        revision = str(int(round(time.time() * 1000)))
        family_name = family_name + "-" + revision

        env_list = []
        for key, value in env_vars_dict.iteritems():
            environment_dict = {}
            environment_dict['name'] = key
            environment_dict['value'] = value
            env_list.append(environment_dict)

        if host_port != 80:
            env_obj = env_db.Environment().get(app_info['env_id'])
            env_output_config = ast.literal_eval(env_obj.output_config)
            sec_group_name = env_output_config['http-and-ssh-group-name']
            sec_group_id = env_output_config['http-and-ssh-group-id']
            vpc_id = env_output_config['vpc_id']

            vpc_traffic_block = []
            internet_traffic = '0.0.0.0/0'
            vpc_traffic_block.append(internet_traffic)
            port_list = [host_port]
            ECSHandler.awshelper.setup_security_group(vpc_id, vpc_traffic_block,
                                                      sec_group_id, sec_group_name, port_list)

        try:
            resp = self.ecs_client.register_task_definition(
                family=family_name,
                containerDefinitions=[{'name': cont_name,
                                       'image': image,
                                       'memory': memory,
                                       'portMappings': [{
                                           'containerPort': container_port,
                                           'hostPort': host_port,
                                           'protocol': 'tcp'}],
                                        'environment': env_list}]
            )
            task_def_arn = resp['taskDefinition']['taskDefinitionArn']
        except Exception as e:
            fmlogger.error("Exception encountered in trying to register task definition:%s" % e)
        fmlogger.debug("Done registering task definition.")
        return task_def_arn, cont_name
    
    def _deregister_task_definition(self, task_def_arn):
        try:
            self.ecs_client.deregister_task_definition(taskDefinition=task_def_arn)
        except Exception as e:
            fmlogger.error("Exception encountered in deregistering task definition:%s" % e)

    def _get_app_url(self, app_info, cluster_name, host_port):
        app_url = ''
        self._copy_creds(app_info)
        df = self.docker_handler.get_dockerfile_snippet("aws")
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "RUN sudo apt-get update && sudo apt-get install -y curl \n"
                   "RUN sudo curl -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-v0.6.2 \ \n"
                   " && chmod +x /usr/local/bin/ecs-cli \n"
                   "ENTRYPOINT [\"ecs-cli\", \"ps\", \"--cluster\", \"{cluster_name}\"]").format(cluster_name=cluster_name)

        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']
        cont_name = app_info['app_name'] + "-get-cont-ip"

        df_dir = app_dir + "/" + app_folder_name
        fp = open(df_dir + "/Dockerfile.get-cont-ip", "w")
        fp.write(df)
        fp.close()

        err, output = self.docker_handler.build_container_image(cont_name, df_dir + "/Dockerfile.get-cont-ip",
                                                                df_context=df_dir)
        app_ip = ''
        if not err:
            run_err, run_output = self.docker_handler.run_container(cont_name)
            if not run_err:
                get_ip_cont_id = run_output.strip()
                logs_err, logs_output = self.docker_handler.get_logs(get_ip_cont_id)
                if not logs_err:
                    task_name = app_info['app_name']
                    lines = logs_output.split("\n")
                    for line in lines:
                        str1 = ' '.join(line.split())
                        parts = str1.split(" ")
                        if len(parts) >= 4:
                            if parts[3].strip().find(task_name) >= 0:
                                if parts[1].strip() == 'RUNNING':
                                    app_url_str = parts[2].strip()
                                    app_ip = app_url_str.split("->")[0].strip()
                                    app_url = "http://" + app_ip
                                    break
                        else:
                            app_url = "Could not get app url."
                            break
                self.docker_handler.remove_container(get_ip_cont_id)
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
                fmlogger.error("Exception encountered in trying to run describe_tasks:%s" % e)
                issue_encountered = True
        return task_desc

    def _stop_task(self, app_id):
        app_obj = app_db.App().get(app_id)
        app_details = app_obj.output_config
        app_details_obj = ast.literal_eval(app_details)

        cluster_name = app_details_obj['cluster_name']
        
        # TODO(devdatta): When we support multiple instances of a task then
        # we should revisit following logic.
        tasks = self.ecs_client.list_tasks(cluster=cluster_name)
        if 'taskArns' in tasks:
            task_arn = tasks['taskArns'][0]  # assuming one task current
            try:
                self.ecs_client.stop_task(cluster=cluster_name, task=task_arn)
            except Exception as e:
                fmlogger.error("Exception encountered in trying to stop_task:%s" % e)

            self._check_task(cluster_name, task_arn, 'stopped')

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
            fmlogger.error("Exception encountered in trying to run_task:%s" % e)

        task_desc = self._check_task(cluster_name, task_arn, 'running')

        container_ip = task_desc['tasks'][0]['containers'][0]['networkBindings'][0]['bindIP']
        host_port = task_desc['tasks'][0]['containers'][0]['networkBindings'][0]['hostPort']

        fmlogger.debug("Container IP:%s" % container_ip)
        fmlogger.debug("Container Port:%s" % host_port)
        application_url = self._get_app_url(app_info, cluster_name, host_port)
        fmlogger.debug("Completed Running task")

        return application_url, task_arn, cluster_name

    def _get_path_for_dfs(self, app_info):
        app_dir = app_info['app_location']
        app_folder_name = app_info['app_folder_name']

        df_dir = app_dir + "/" + app_folder_name
        return df_dir

    def _copy_creds(self, app_info, provided_df_dir=''):
        df_dir = provided_df_dir
        if not df_dir:
            df_dir = self._get_path_for_dfs(app_info)

        if not os.path.exists(df_dir + "/aws-creds"):
            shutil.copytree(home_dir + "/.aws", df_dir + "/aws-creds")

    def _update_ecs_app_service(self, app_info, cont_name, task_def_arn, task_desired_count=1):
        cluster_name = self._get_cluster_name(app_info['env_id'])
        ECSHandler.awshelper.update_service(app_info['app_name'], cluster_name,
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
        env_obj = env_db.Environment().get(app_info['env_id'])
        env_output_config = ast.literal_eval(env_obj.output_config)
        subnet_string = env_output_config['subnets']
        subnet_list = subnet_string.split(',')
        sec_group_id = env_output_config['http-and-ssh-group-id']
        vpc_id = env_output_config['vpc_id']
        cluster_name = self._get_cluster_name(app_info['env_id'])
        app_ports = common_functions.get_app_port(app_info)
        container_port = app_ports[0]
        host_port = app_ports[1]
        app_url, lb_arn, target_group_arn, listener_arn = ECSHandler.awshelper.create_service(
            app_info['app_name'], container_port, host_port, vpc_id,
            subnet_list, sec_group_id, cluster_name,
            task_def_arn, cont_name
        )
        app_ip_url = self._get_app_url(app_info, cluster_name, host_port)
        if not app_url:
            app_url = app_ip_url
        else:
            app_url = "http://" + app_url
        fmlogger.debug("App URL:%s" % app_url)
        fmlogger.debug("App IP URL:%s" % app_ip_url)

        return app_url, app_ip_url, lb_arn, target_group_arn, listener_arn

    def _get_container_port(self, task_def_arn):
        container_port = ECSHandler.awshelper.get_container_port_from_taskdef(task_def_arn)
        return container_port

    def delete_cluster(self, env_id, env_info, resource, available_cluster_name=''):
        cluster_name = ''
        if resource:
            cluster_name = resource.cloud_resource_id
        elif available_cluster_name:
            cluster_name = available_cluster_name
        else:
            fmlogger.error("No cluster name given. Returning")
            return

        df = self.docker_handler.get_dockerfile_snippet("aws")
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "RUN sudo apt-get update && sudo apt-get install -y curl \n"
                   "RUN sudo curl -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-v0.6.2 \ \n"
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
        else:
            fmlogger.debug("Done deleting ECS cluster %s" % cluster_name)

        self.docker_handler.remove_container(cont_name)
        self.docker_handler.remove_container_image(cont_name)

        ec2 = boto3.resource('ec2')
        key_pair = ec2.KeyPair(cluster_name)
        try:
            key_pair.delete()
        except Exception as e:
            fmlogger.error("Error encountered in deleting key pair. %s" % e)

        try:
            self.ecs_client.delete_cluster(cluster=cluster_name)
        except Exception as e:
            fmlogger.error("Error encountered in deleting cluster %s" % e)

        env_obj = env_db.Environment().get(env_id)
        try:
            env_output_config = ast.literal_eval(env_obj.output_config)
            sec_group_name = env_output_config['http-and-ssh-group-name']
            sec_group_id = env_output_config['http-and-ssh-group-id']
            vpc_id = env_output_config['vpc_id']
            ECSHandler.awshelper.delete_security_group_for_vpc(vpc_id, sec_group_id, sec_group_name)
        except Exception as e:
            fmlogger.error(e)

        res_db.Resource().delete(res_id)

    def _get_cluster_ips(self, cluster_name, env_store_location):
        cluster_instance_ip_list = []
        df = self.docker_handler.get_dockerfile_snippet("aws")
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \ \n"
                        " && aws ec2 describe-instances")
        fp = open(env_store_location + "/Dockerfile.get-instance-ip", "w")
        fp.write(df)
        fp.flush()
        fp.close()

        get_ip_cont_image = cluster_name+"get-ip"
        err, output = self.docker_handler.build_container_image(get_ip_cont_image,
                                                                env_store_location + "/Dockerfile.get-instance-ip",
                                                                df_context=env_store_location)

        if err:
            fmlogger.error("Error encountered in building container image to get cluster IP address. %s " + str(err))
            return

        output_lines = output.split('\n')
        json_lines = []
        start = False
        for line in output_lines:
            if not start:
                if len(line) == 1 and line == '{':
                    start = True
                    json_lines.append(line)
            else:
                json_lines.append(line)
        for line in json_lines[::-1]:
            if not line == '}':
                del json_lines[-1]
            else:
                break

        json_string = '\n'.join(json_lines)
        json_string = re.sub('\s+', '', json_string)
        json_output = json.loads(json_string)

        reservations = json_output['Reservations']
        for res_item in reservations:
            instances = res_item['Instances']
            for instance in instances:
                if 'KeyName' in instance:
                    key_name = instance['KeyName']
                    if key_name == cluster_name:
                        cluster_instance_ip_list.append(instance['PublicIpAddress'])

        # Delete the container created for obtaining IP address
        self.docker_handler.remove_container_image(get_ip_cont_image)

        return cluster_instance_ip_list

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
        shutil.copytree(home_dir + "/.aws", env_store_location + "/aws-creds")
        
        # 1) Cluster vpc details handling
        vpc_id = ''
        subnet_ids = ''
        try:
            vpc_details = ECSHandler.awshelper.get_vpc_details()
        except Exception as e:
            fmlogger.error("Error occurred when trying to get vpc details %s" + str(e))
            error_message = 'provisioning-failed: ' + str(e)
            env_db.Environment().update(env_id, {'output_config': error_message,
                                                 'status': 'create-failed'})
        vpc_id = vpc_details['vpc_id']
        cidr_block = vpc_details['cidr_block']
        subnet_ids = ''
        try:
            subnet_ids = ECSHandler.awshelper.get_subnet_ids(vpc_id)
        except Exception as e:
            fmlogger.error("Error occurred when trying to get subnet ids %s" + str(e))
            error_message = 'provisioning-failed: ' + str(e)
            env_db.Environment().update(env_id, {'output_config': error_message,
                                                 'status': 'create-failed'})            
        subnet_list = ','.join(subnet_ids)
        sec_group_name = cluster_name + "-http-ssh"
        sec_group_id = ''
        try:
            sec_group_id = ECSHandler.awshelper.create_security_group_for_vpc(vpc_id, sec_group_name)
        except Exception as e:
            fmlogger.error("Error occurred when trying to create security group for vpc %s" + str(e))
            error_message = 'provisioning-failed: ' + str(e)
            env_db.Environment().update(env_id, {'output_config': error_message,
                                                 'status': 'create-failed'})
        env_output_config['subnets'] = subnet_list
        env_output_config['vpc_id'] = vpc_id
        env_output_config['cidr_block'] = cidr_block
        env_output_config['http-and-ssh-group-name'] = sec_group_name
        env_output_config['http-and-ssh-group-id'] = sec_group_id
        env_update = {}
        env_update['status'] = env_obj.status
        env_update['output_config'] = str(env_output_config)
        env_db.Environment().update(env_id, env_update)

        vpc_traffic_block = []
        internet_traffic = '0.0.0.0/0'
        vpc_traffic_block.append(internet_traffic)
        port_list = [22, 80]
        try:
            ECSHandler.awshelper.setup_security_group(vpc_id, vpc_traffic_block,
                                                      sec_group_id, sec_group_name, port_list)
        except Exception as e:
            fmlogger.error("Error occurred when trying to setup security group for vpc %s" + str(e))
            error_message = 'provisioning-failed: ' + str(e)
            try:
                ECSHandler.awshelper.delete_security_group_for_vpc(vpc_id, sec_group_id, sec_group_name)
            except Exception as e1:
                fmlogger.error(e1)
                error_message = error_message + " + " + str(e1)
                env_db.Environment().update(env_id, {'output_config': error_message,
                                                     'status': 'create-failed'})            
            
        # 2) Creating the cluster
        region, access_key, secret_key = ECSHandler.get_aws_details()
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
        entry_point_cmd = (
            "ENTRYPOINT [\"ecs-cli\", \"up\", \"--size\", \"{size}\", \"--keypair\", \"{keypair}\", \"--capability-iam\", \"--vpc\", \"{vpc_id}\", \"--subnets\", \"{subnet_list}\", "
            "\"--security-group\", \"{security_group}\", \"--instance-type\", \"{instance_type}\", \"--cluster\", \"{cluster}\"] \n").format(
                size=cluster_size,
                cluster=cluster_name, vpc_id=vpc_id,
                keypair=keypair_name,
                security_group=sec_group_id,
                subnet_list=subnet_list,
                instance_type=instance_type
        )
        fmlogger.debug("Entry point cmd:%s" % entry_point_cmd)
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "RUN sudo apt-get update && sudo apt-get install -y curl \n"
                   "{create_keypair_cmd} \n"
                   "RUN sudo curl -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-v0.6.2 \ \n"
                   " && chmod +x /usr/local/bin/ecs-cli \ \n"
                   " && ecs-cli configure --region {reg} --cluster {cluster} \n"
                   " {entry_point_cmd}"
                   ).format(create_keypair_cmd=create_keypair_cmd, reg=region,
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
        if err:
            error_output = common_functions.filter_error_output(image_id)
            error_message = 'provisioning-failed: ' + error_output
            res_data['status'] = error_message
            res_db.Resource().update(res_id, res_data)
            try:
                ECSHandler.awshelper.delete_security_group_for_vpc(vpc_id, sec_group_id, sec_group_name)
            except Exception as e1:
                fmlogger.error(e1)
                error_message = error_message + " + " + str(e1)
                env_db.Environment().update(env_id, {'output_config': error_message,
                                                     'status': 'create-failed'})
            env_db.Environment().update(env_id, {'output_config': error_message})
            return error_message

        err, cont_id = self.docker_handler.run_container(cluster_name)

        if err:
            error_output = common_functions.filter_error_output(err)
            error_message = 'provisioning-failed: ' + error_output
            res_data['status'] = error_message
            res_db.Resource().update(res_id, res_data)
            try:
                ECSHandler.awshelper.delete_security_group_for_vpc(vpc_id, sec_group_id, sec_group_name)
            except Exception as e1:
                fmlogger.error(e1)
                error_message = error_message + " + " + str(e1)
                env_db.Environment().update(env_id, {'output_config': error_message,
                                                     'status': 'create-failed'})
            env_db.Environment().update(env_id, {'output_config': error_message})
            return error_message

        cont_id = cont_id.rstrip().lstrip()

        log_lines = []
        error_found = False
        new_lines_found = True
        while new_lines_found:
            logs = self.docker_handler.get_logs(cont_id)
            new_lines_found, new_lines = common_functions.are_new_log_lines(logs, log_lines)
            log_lines.extend(new_lines)
            error_found, error_message = common_functions.is_error_in_log_lines(logs)
            if error_found:
                env_db.Environment().update(env_id, {'output_config': error_message,
                                                     'status': 'create-failed'})
                return error_message
            else:
                status_message = ', '.join(log_lines)
                env_db.Environment().update(env_id, {'output_config': status_message,
                                                     'status': 'provisioning'})

        fmlogger.debug("Checking status of ECS cluster %s" % cluster_name)
        is_active = False
        failures = ''
        while not is_active:
            try:
                clusters_dict = self.ecs_client.describe_clusters(clusters=[cluster_name])
                registered_instances_count = clusters_dict['clusters'][0]['registeredContainerInstancesCount']
                if registered_instances_count == cluster_size:
                    is_active = True
                    cluster_status = 'available'
                    break
                
                # Revisit the following code.
                # Currently failures will never be set. We will need this only if describe_clusters ever
                # encounters a failure.
                #if 'failures' in clusters_dict:
                #    failures = clusters_dict['failures']
                #    break
            except Exception as e:
                fmlogger.debug("Exception encountered in trying to describe clusters:%s" % e)
            time.sleep(2)

        res_db.Resource().update(res_id, {'status': cluster_status})

        if failures:
            cluster_status = 'provisioning-failure' + str(failures)
            fmlogger.error("Failed to provision ECS cluster.")
            res_db.Resource().update(res_id, {'status': cluster_status})
            
            try:
                ECSHandler.awshelper.delete_security_group_for_vpc(vpc_id, sec_group_id, sec_group_name)
            except Exception as e1:
                fmlogger.error(e1)
                error_message = error_message + " + " + str(e1)
                env_db.Environment().update(env_id, {'output_config': error_message,
                                                     'status': 'create-failed'})            
            return cluster_status

        env_output_config['cluster_name'] = cluster_name
        env_update['output_config'] = str(env_output_config)
        env_db.Environment().update(env_id, env_update)
        env_db.Environment().update(env_id, env_update)

        cp_cmd = ("docker cp {cont_id}:/src/{key_file}.pem {env_dir}/.").format(cont_id=cont_id,
                                                                                env_dir=env_store_location,
                                                                                key_file=keypair_name)
        os.system(cp_cmd)

        self.docker_handler.stop_container(cluster_name)
        self.docker_handler.remove_container(cont_id)
        self.docker_handler.remove_container_image(cluster_name)

        env_update = {}
        env_output_config['key_file'] = env_store_location + "/" + keypair_name + ".pem"
        env_update['output_config'] = str(env_output_config)
        env_db.Environment().update(env_id, env_update)

        instance_ip_list = self._get_cluster_ips(cluster_name, env_store_location)
        if not instance_ip_list:
            error_message = "Could not get Cluster instance IP. Not continuing with the request."
            fmlogger.error(error_message)
            env_update['status'] = error_message + " Deleting the cluster."
            env_db.Environment().update(env_id, env_update)
            self.delete_cluster(env_id, env_info, '', available_cluster_name=cluster_name)
            return error_message
        else:
            env_output_config['cluster_ips'] = instance_ip_list
            env_update['status'] = cluster_status
            env_update['output_config'] = str(env_output_config)
            env_db.Environment().update(env_id, env_update)
            fmlogger.debug("Done creating ECS cluster %s" % cluster_name)
            return cluster_status

    def deploy_application(self, app_id, app_info):
        self._copy_creds(app_info)

        env_vars = common_functions.resolve_environment(app_id, app_info)

        app_details = {}
        app_data = {}
        app_details['task-familyName'] = app_info['app_name']
        app_data['status'] = 'registering-task-definition'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        tagged_image = common_functions.get_image_uri(app_info)

        app_ports = common_functions.get_app_port(app_info)
        container_port = int(app_ports[0])
        host_port = int(app_ports[1])
        task_def_arn, cont_name = self._register_task_definition(app_info, tagged_image,
                                                                 container_port, host_port,
                                                                 env_vars)
        app_details['task_def_arn'] = [task_def_arn]
        app_details['cont_name'] = cont_name
        app_details['cluster_name'] = self._get_cluster_name(app_info['env_id'])
        app_details['image_name'] = [tagged_image]
        app_details['memory'] = common_functions.get_app_memory(app_info)
        app_details['app_folder_name'] = app_info['app_folder_name']
        app_details['env_name'] = app_info['env_name']
        app_details['container_port'] = container_port
        app_details['host_port'] = host_port

        app_data['status'] = 'creating-ecs-app-service'
        app_data['output_config'] = str(app_details)
        app_db.App().update(app_id, app_data)

        app_url = app_ip_url = lb_arn = target_group_arn = listener_arn = ''

        try:
            app_url, app_ip_url, lb_arn, target_group_arn, listener_arn = self._create_ecs_app_service(
                app_info,
                cont_name,
                task_def_arn
            )
        except Exception as e: #exceptions.ECSServiceCreateTimeout as e:
            fmlogger.error(e)
            app_details['error'] = str(e) #e.get_message()
            app_data = {}
            app_data['output_config'] = str(app_details)
            app_db.App().update(app_id, app_data)
            return

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

    def redeploy_application(self, app_id, app_info):
        self._copy_creds(app_info)

        #if app_info['env_id']:
        env_vars = common_functions.resolve_environment(app_id, app_info)

        app_obj = app_db.App().get(app_id)
        app_details = app_obj.output_config
        app_details_obj = ast.literal_eval(app_details)

        app_dt = {}
        app_dt['status'] = 'redeploying'
        app_dt['output_config'] = str(app_details_obj)
        app_db.App().update(app_id, app_dt)

        if 'memory' in app_details_obj:
            app_info['memory'] = app_details_obj['memory']
        proxy_endpoint = app_details_obj['proxy_endpoint']
        repo_name = app_details_obj['repo_name']
        tag = str(int(round(time.time() * 1000)))

        app_dt['status'] = 'building-app-container'
        app_db.App().update(app_id, app_dt)
        err, output, image_name = self._build_app_container(app_info, repo_name, proxy_endpoint, tag=tag)
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request.")
            return

        app_dt['status'] = 'pushing-app-cont-to-ecr-repository'
        app_db.App().update(app_id, app_dt)

        tagged_image = image_name + ":" + tag
        err, output = self.docker_handler.push_container(tagged_image)

        common_functions.save_image_tag(tagged_image, app_info)
        if err:
            fmlogger.debug("Error encountered in pushing container image to ECR. Not continuing with the request.")

            app_dt['status'] = 'error-encountered-in-pushing-app-cont-image'
            app_db.App().update(app_id, app_dt)
            raise Exception()
        fmlogger.debug("Completed pushing container %s to AWS ECR" % tagged_image)

        current_task_def_arn = app_details_obj['task_def_arn'][-1]
        container_port = self._get_container_port(current_task_def_arn)
        host_port = 80
        orig_cont_name = app_details_obj['cont_name']

        app_dt['status'] = 'deregistering-current-task-ecs-app-service'
        app_db.App().update(app_id, app_dt)

        self._update_ecs_app_service(app_info, orig_cont_name, current_task_def_arn, task_desired_count=0)

        app_dt['status'] = 'registering-new-task-ecs-app-service'
        app_db.App().update(app_id, app_dt)
        new_task_def_arn, cont_name = self._register_task_definition(app_info, tagged_image,
                                                                     container_port, host_port, env_vars,
                                                                     cont_name=orig_cont_name)
        self._update_ecs_app_service(app_info, orig_cont_name, new_task_def_arn, task_desired_count=1)

        app_details_obj['task_def_arn'].append(new_task_def_arn)
        app_details_obj['image_name'].append(tagged_image)

        app_ip_url = app_details_obj['app_ip_url']
        app_url = app_details_obj['app_url']

        app_dt['status'] = 'waiting-for-app-to-get-ready'
        app_db.App().update(app_id, app_dt)

        status = self._check_if_app_is_ready(app_id, app_ip_url, app_url)

        app_dt['status'] = status
        app_db.App().update(app_id, app_dt)

    def delete_application(self, app_id, app_info):
        fmlogger.debug("Deleting Application:%s" % app_id)
        app_obj = app_db.App().get(app_id)

        try:
            app_details = app_obj.output_config
            app_details_obj = ast.literal_eval(app_details)
            app_details_obj['app_url'] = ''

            app_dt = {}
            app_dt['status'] = 'deleting'
            app_dt['output_config'] = str(app_details_obj)
            app_db.App().update(app_id, app_dt)

            try:
                task_def_arn_list = app_details_obj['task_def_arn']
                latest_task_def_arn = task_def_arn_list[-1]
                cont_name = app_details_obj['cont_name']
                self._update_ecs_app_service(app_info, cont_name, latest_task_def_arn, task_desired_count=0)
                for task_def_arn in task_def_arn_list:
                    self._deregister_task_definition(task_def_arn)
                self.ecs_client.delete_service(cluster=app_details_obj['cluster_name'],
                                               service=app_obj.name)
            except Exception as e:
                fmlogger.error("Exception encountered in trying to delete ecs service %s" % e)

            ECSHandler.awshelper.delete_listener(app_details_obj)

            ECSHandler.awshelper.delete_target_group(app_details_obj)

            ECSHandler.awshelper.delete_load_balancer(app_details_obj)

            try:
                tagged_image_list = app_details_obj['image_name']
                if tagged_image_list:
                    for tagged_image in tagged_image_list:
                        self.docker_handler.remove_container_image(tagged_image)
            except Exception as e:
                fmlogger.error("Exception encountered while deleting images %s" % e)

        except Exception as e:
            fmlogger.error("Exception encountered while deleting images %s" % e)

        app_db.App().delete(app_id)

    def _retrieve_runtime_logs(self, cluster_ip, app_name, logs_path, df_dir, pem_file_name):
        runtime_log = cluster_ip + constants.RUNTIME_LOG
        runtime_log_path = logs_path + "/" + runtime_log

        mkdir_command = ("mkdir {logs_path}").format(logs_path=runtime_log_path)
        fmlogger.debug(mkdir_command)
        os.system(mkdir_command)

        app_obj = app_db.App().get_by_name(app_name)
        output_config = ast.literal_eval(app_obj.output_config)
        tagged_images = output_config['image_name']
        image = tagged_images[0]

        dockerlogs_sh = "dockerlogs.sh"
        if not os.path.exists(df_dir + "/" + dockerlogs_sh):
            fp = open(df_dir + "/" + dockerlogs_sh, "w")
            file_content = ("#!/bin/bash \n"
                            "sudo docker ps | grep {image} | awk '{{print $1}}' | xargs docker logs \n"
                           ).format(image=image)
            fp.write(file_content)
            fp.flush()
            fp.close()

        ssh_wrapper = "ssh_wrapper.sh"
        ssh_wrapper_path = df_dir + "/" + ssh_wrapper
        if not os.path.exists(ssh_wrapper_path):
            fp = open(ssh_wrapper_path, "w")
            file_content = ("#!/bin/bash \n"
                            "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i "
                            "/root/.ssh/{pem_file_name} ec2-user@{cluster_ip} 'bash -s' < {dockerlogs_sh}").format(
                             pem_file_name=pem_file_name, cluster_ip=cluster_ip, dockerlogs_sh=dockerlogs_sh)
            fp.write(file_content)
            fp.flush()
            fp.close()
            change_perm_command = ("chmod +x {ssh_wrapper_path}").format(ssh_wrapper_path=ssh_wrapper_path)
            os.system(change_perm_command)

        dockerfile_name = "Dockerfile.retrieve-logs-" + runtime_log
        df_path = df_dir + "/" + dockerfile_name
        if not os.path.exists(df_path):
            df = self.docker_handler.get_dockerfile_snippet("aws")
            df = df + ("COPY . /src \n"
                       "WORKDIR /src \n"
                       "RUN sudo apt-get install -y openssh-client \n"
                       "RUN cp -r aws-creds $HOME/.aws \ \n"
                       " && mkdir /root/.ssh \ \n"
                       " && cp /src/{pem_file_name} /root/.ssh/. \ \n"
                       " && chmod 400 /root/.ssh/{pem_file_name} \ \n"
                       " && ./ssh_wrapper.sh"
                       ).format(pem_file_name=pem_file_name)
            fp = open(df_path, "w")

            fp.write(df)
            fp.flush()
            fp.close()

        log_cont_name = ("{app_name}-{cluster_ip}-retrieve-run-logs").format(app_name=app_name,
                                                                             cluster_ip=cluster_ip)
        err, output = self.docker_handler.build_container_image(log_cont_name, df_path, df_context=df_dir)
        if not err:
            filtered_output = self.docker_handler.filter_output(output)
            log_output_string = '\n'.join(filtered_output)

            fp2 = open(runtime_log_path + "/runtime.log", "w")
            fp2.write(log_output_string)
            fp2.flush()
            fp2.close()

            self.docker_handler.remove_container_image(log_cont_name)

        return runtime_log_path

    def _retrieve_deploy_logs(self, cluster_ip, app_name, logs_path, df_dir, pem_file_name):
        deploy_log = cluster_ip + constants.DEPLOY_LOG
        deploy_log_path = logs_path + "/" + deploy_log

        mkdir_command = ("mkdir {logs_path}").format(logs_path=deploy_log_path)
        fmlogger.debug(mkdir_command)
        os.system(mkdir_command)

        logs_path_cont = '/src/' + deploy_log
        scp_cmd = ("ENTRYPOINT [\"scp\", \"-rp\", \"-o\", \"UserKnownHostsFile=/dev/null\", \"-o\", \"StrictHostKeyChecking=no\", "
                   "\"-i\", \"/root/.ssh/{pem_file_name}\", \"ec2-user@{public_ip}:/var/log/ecs\", \"{logs_path}\" ]"
                   ).format(pem_file_name=pem_file_name, public_ip=cluster_ip, logs_path=".")

        dockerfile_name = "Dockerfile.retrieve-logs-" + deploy_log
        df_path = df_dir + "/" + dockerfile_name

        if not os.path.exists(df_path):
            df = self.docker_handler.get_dockerfile_snippet("aws")
            df = df + ("COPY . /src \n"
                       "WORKDIR /src \n"
                       "RUN sudo apt-get install -y openssh-client \n"
                       "RUN cp -r aws-creds $HOME/.aws \ \n"
                       " && mkdir /root/.ssh \ \n"
                       " && cp /src/{pem_file_name} /root/.ssh/. \ \n"
                       " && chmod 400 /root/.ssh/{pem_file_name}  \n"
                       " {scp_command}"
                       ).format(pem_file_name=pem_file_name, scp_command=scp_cmd)
            fp = open(df_path, "w")

            fp.write(df)
            fp.flush()
            fp.close()

        log_cont_name = ("{app_name}-{cluster_ip}-retrieve-deploy-logs").format(app_name=app_name,
                                                                                cluster_ip=cluster_ip)
        err, output = self.docker_handler.build_container_image(log_cont_name, df_path, df_context=df_dir)

        if not err:
            run_err, run_output = self.docker_handler.run_container(log_cont_name)
            if not run_err:
                logs_cont_id = run_output.strip()

                time.sleep(5) # Allow time to retrieve the logs
                logs_cp_cmd = ("docker cp {cont_id}:{logs_path_cont} {logs_path}/").format(cont_id=logs_cont_id,
                                                                                           logs_path_cont="/src/ecs",
                                                                                           logs_path=deploy_log_path)
                fmlogger.debug(logs_cp_cmd)
                os.system(logs_cp_cmd)

                self.docker_handler.stop_container(logs_cont_id)
                self.docker_handler.remove_container(logs_cont_id)
                self.docker_handler.remove_container_image(log_cont_name)
        return deploy_log_path

    def _retrieve_logs(self, app_info):
        env_obj = env_db.Environment().get(app_info['env_id'])
        env_output_config = ast.literal_eval(env_obj.output_config)
        cluster_ips = env_output_config['cluster_ips']
        cluster_name = env_output_config['cluster_name']
        pem_file = env_output_config['key_file']

        app_name = app_info['app_name']
        app_location = app_info['app_location']

        self._copy_creds(app_info, provided_df_dir=app_location)

        df_dir = app_location
        logs_path = app_info['app_location'] + "/logs"
        logs_path_cmd = ("mkdir {logs_path}").format(logs_path=logs_path)
        os.system(logs_path_cmd)

        pem_file_name = ("{cluster_name}.pem").format(cluster_name=cluster_name)
        copy_pem_file = ("cp {pem_file} {df_dir}/{pem_file_name}").format(pem_file=pem_file,
                                                                          df_dir=df_dir,
                                                                          pem_file_name=pem_file_name)
        fmlogger.debug(copy_pem_file)
        os.system(copy_pem_file)

        logs_path_list = []
        for cluster_ip in cluster_ips:
            deploy_logs_path = self._retrieve_deploy_logs(cluster_ip, app_name, logs_path,
                                                          df_dir, pem_file_name)
            runtime_logs_path = self._retrieve_runtime_logs(cluster_ip, app_name, logs_path,
                                                            df_dir, pem_file_name)
            logs_path_list.append(deploy_logs_path)
            logs_path_list.append(runtime_logs_path)
        return logs_path_list

    def get_logs(self, app_id, app_info):
        fmlogger.debug("Retrieving logs for application %s %s" % (app_id, app_info['app_name']))
        logs_path_list = self._retrieve_logs(app_info)
        return logs_path_list

    def run_command(self, env_id, env_name, resource_obj, command):
        fmlogger.debug("Running command against ECS cluster")

        if command.lower() == 'help':
            return ECSHandler.help_commands

        command_output = ''

        is_supported_command = self._verify(command)
        if not is_supported_command:
            command_output = ["Command not supported"]
            return command_output

        command_output = ECSHandler.awshelper.run_command(env_id, env_name, resource_obj, command)

        output_lines = command_output.split("\n")

        return output_lines
