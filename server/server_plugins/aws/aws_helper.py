import boto3
import os
import time

from server.common import constants
from server.common import docker_lib
from server.common import exceptions
from server.common import fm_logger

from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db

fmlogger = fm_logger.Logging()


class AWSHelper(object):

    def __init__(self):
        self.ecr_client = boto3.client('ecr')
        self.ecs_client = boto3.client('ecs')
        self.ec2_client = boto3.client('ec2')
        self.alb_client = boto3.client('elbv2')
        self.iam_client = boto3.client('iam')
        self.docker_handler = docker_lib.DockerLib()

    def _create_application_lb(self, app_name, subnet_list, sec_group_list):
        fmlogger.debug("Creating application load balancer for app:%s" % app_name)
        lb_dns = ''
        lb_arn = ''
        try:
            response = self.alb_client.create_load_balancer(Name=app_name, Subnets=subnet_list,
                                                            SecurityGroups=sec_group_list,
                                                            Scheme='internet-facing',
                                                            IpAddressType='ipv4')
            lb_dns = response['LoadBalancers'][0]['DNSName']
            lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
        except Exception as e:
            fmlogger.error("Encountered exception in creating application load balancer:%s" % e)
            raise e

        fmlogger.debug("Application load balancer creation done. LB DNS:%s" % lb_dns)
        return lb_arn, lb_dns

    def _create_target_group(self, app_name, app_port, vpc_id):
        fmlogger.debug("Creating lb target group for app:%s" % app_name)
        target_group_arn = ''
        target_group_name = ''
        try:
            response = self.alb_client.create_target_group(Name=app_name, Protocol='HTTP',
                                                           Port=int(app_port), VpcId=vpc_id)
            target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
            target_group_name = response['TargetGroups'][0]['TargetGroupName']
        except Exception as e:
            fmlogger.error("Encountered exception in creating target group:%s" % e)
            raise e
        
        fmlogger.debug("lb target group creation done. target_group_arn:%s target_group_name:%s" % (target_group_arn, target_group_name))
        return target_group_arn, target_group_name

    def _create_lb_listener(self, host_port, load_balancer_arn, target_group_arn):
        fmlogger.debug("Creating lb listener.")
        listener_arn = ''
        try:
            response = self.alb_client.create_listener(LoadBalancerArn=load_balancer_arn,
                                                       Protocol='HTTP',
                                                       Port=host_port,
                                                       DefaultActions=[{'Type': 'forward',
                                                                        'TargetGroupArn': target_group_arn}])
            listener_arn = response['Listeners'][0]['ListenerArn']
        except Exception as e:
            fmlogger.error("Encountered exception in creating a lb listener %s" % e)
            raise e

        fmlogger.debug("Done creating lb listener.")
        return listener_arn

    def get_vpc_details(self, search_key='default'):
        vpc_id = ''
        vpc_details = {}

        try:
            response = self.ec2_client.describe_vpcs()

            def _search_tags(tags_list, search_key):
                for tag in tags_list:
                    for key, value in tag.iteritems():
                        if key.lower().find(search_key.lower()) >= 0:
                            return True
                        if value.lower().find(search_key.lower()) >= 0:
                            return True

            vpc_list = response['Vpcs']
            target_vpc = ''
            for vpc in vpc_list:
                default_status = vpc['IsDefault']
                tags = []
                if 'Tags' in vpc:
                    tags = vpc['Tags']
                if search_key == 'default' and default_status:
                    target_vpc = vpc
                elif _search_tags(tags, search_key):
                    target_vpc = vpc
            vpc_id = target_vpc['VpcId']
            cidr_block = target_vpc['CidrBlock']

            vpc_details['vpc_id'] = vpc_id
            vpc_details['cidr_block'] = cidr_block
        except Exception as e:
            fmlogger.error("Encountered exception in getting vpc details %s" % e)
            raise e

        return vpc_details
    
    def get_cidr_block(self, vpc='default'):
        fmlogger.debug("Getting cidr block for vpc:%s" % vpc)
        cidr_block = ''
        if vpc == 'default':
            pass

        return cidr_block
    
    def get_subnet_ids(self, vpc_id, search_key='default'):
        fmlogger.debug("Getting subnet ids for VPC %s" % search_key)
        subnet_ids = []
        
        try:
            response = self.ec2_client.describe_subnets()
            subnet_list = response['Subnets']
            for subnet in subnet_list:
                if subnet['VpcId'] == vpc_id:
                    subnet_ids.append(subnet['SubnetId'])
        except Exception as e:
            fmlogger.error("Encountered exception in getting subnet details %s" % e)
            raise e

        return subnet_ids
    
    def create_security_group_for_vpc(self, vpc_id, group_name):
        fmlogger.debug("Creating security group %s for vpc %s" % (group_name, vpc_id))
        security_group_id = ''

        try:
            response = self.ec2_client.create_security_group(Description=group_name,
                                                             GroupName=group_name,
                                                             VpcId=vpc_id)
            security_group_id = response['GroupId']
        except Exception as e:
            fmlogger.error("Encountered exception in creating security group %s" % e)
            raise e

        return security_group_id

    def delete_security_group_for_vpc(self, vpc_id, group_id, group_name):
        fmlogger.debug("Deleting security group %s for vpc %s" % (group_name, vpc_id))
        try:
            self.ec2_client.delete_security_group(GroupId=group_id, GroupName=group_name)
        except Exception as e:
            fmlogger.error("Encountered exception in deleting security group %s" % e)
            raise e

    def setup_security_group(self, vpc_id, ip_range, sec_group_id, sec_group_name, port_list):
        for ip in ip_range:
            rules_dict = {}
            rules_dict['protocol'] = 'tcp'
            rules_dict['ip_range'] = ip
            for port in port_list:
                rules_dict['to_port'] = port
                self.authorize_security_group_ingress(sec_group_id, sec_group_name, rules_dict)

    def authorize_security_group_ingress(self, group_id, group_name, rules_dict):
        fmlogger.debug("Setting security group rules for group:%s" % group_name)
        protocol = rules_dict['protocol']
        to_port = rules_dict['to_port']
        ip_range = rules_dict['ip_range']

        try:
            self.ec2_client.authorize_security_group_ingress(GroupId=group_id,
                                                             GroupName=group_name,
                                                             IpPermissions=[{'FromPort': 0,
                                                                             'ToPort': to_port,
                                                                             'IpRanges': [{'CidrIp': ip_range}],
                                                                             'IpProtocol': protocol}])
        except Exception as e:
            fmlogger.debug("Encountered exception in adding rule to security group:%s" % e)
            raise e
        return

    def get_container_port_from_taskdef(self, task_def_arn):
        container_port = 0
        try:
            response = self.ecs_client.describe_task_definition(taskDefinition=task_def_arn)
            container_port = response['taskDefinition']['containerDefinitions'][0]['portMappings'][0]['containerPort']
        except Exception as e:
            fmlogger.error("Encountered exception in describing task definition %s" % e)
        return int(container_port)

    def update_service(self, app_name, cluster_name, task_def_arn, task_desired_count):
        try:
            self.ecs_client.update_service(cluster=cluster_name,
                                           service=app_name,
                                           desiredCount=task_desired_count,
                                           taskDefinition=task_def_arn)
        except Exception as e:
            fmlogger.debug("Exception encountered in updating ECS service for app %s" % e)

        service_available = False
        issue_encountered = False
        service_desc = ''

        # Need to stop the task explicitly as just updating the service does not
        # seem to stop the running task:
        if task_desired_count == 0:
            tasks = self.ecs_client.list_tasks(cluster=cluster_name)
            if 'taskArns' in tasks and len(tasks['taskArns']) > 0:
                task_arn = tasks['taskArns'][0]  # assuming one task current
                try:
                    self.ecs_client.stop_task(cluster=cluster_name, task=task_arn)
                except Exception as e:
                    fmlogger.debug("Exception encountered in trying to stop_task")

        while not service_available and not issue_encountered:
            try:
                service_desc = self.ecs_client.describe_services(cluster=cluster_name,
                                                                 services=[app_name])
                pending_count = service_desc['services'][0]['pendingCount']
                running_count = service_desc['services'][0]['runningCount']
                if pending_count == 0 and running_count == task_desired_count:
                    service_available = True
            except Exception as e:
                fmlogger.debug("Exception encountered in trying to run describe_services. %s" % e)
                issue_encountered = True

        return service_available

    def create_service(self, app_name, container_port, host_port, vpc_id, subnet_list, sec_group_id,
                       cluster_name, task_def_arn, container_name):

        app_url = ''
        fmlogger.debug("Creating ECS service for app %s" % app_name)
        sec_group_list = [sec_group_id]
        lb_arn, lb_dns = self._create_application_lb(app_name, subnet_list, sec_group_list)
        target_group_arn, target_group_name = self._create_target_group(app_name, container_port, vpc_id)
        listener_arn = ''
        try:
            listener_arn = self._create_lb_listener(host_port, lb_arn, target_group_arn)
        except Exception as e:
            fmlogging.error(str(e))
            raise e
        desired_count = 1  # Number of tasks default to 1

        role_obj = self.iam_client.get_role(RoleName='EcsServiceRole')
        role_arn = role_obj['Role']['Arn']

        try:
            self.ecs_client.create_service(cluster=cluster_name,
                                           serviceName=app_name,
                                           taskDefinition=task_def_arn,
                                           loadBalancers=[{'targetGroupArn': target_group_arn,
                                                           # 'loadBalancerName': app_name,
                                                           'containerName': container_name,
                                                           'containerPort': int(container_port)}],
                                           desiredCount=desired_count,
                                           role=role_arn)
        except Exception as e:
            fmlogger.debug("Exception encountered in creating ECS service for app %s" % e)
            raise e
        fmlogger.debug("ECS service creation for app %s done." % app_name)

        service_available = False
        service_desc = ''
        service_message = ''
        count = 1
        while not service_available and count < constants.TIMEOUT_COUNT:
            try:
                service_desc = self.ecs_client.describe_services(cluster=cluster_name,
                                                                 services=[app_name])
                pending_count = service_desc['services'][0]['pendingCount']
                running_count = service_desc['services'][0]['runningCount']
                service_message = service_desc['services'][0]['events'][0]['message']

                app_data = {'status': service_message}
                app_db.App().update_by_name(app_name, app_data)

                if pending_count == 0 and running_count == desired_count:
                    service_available = True
                    app_url = lb_dns + ":" + str(host_port)
                    break
            except Exception as e:
                fmlogger.debug("Exception encountered in trying to run describe_services. %s" % e)
            count = count + 1
            time.sleep(2)

        if count == constants.TIMEOUT_COUNT and not service_available:
            raise exceptions.ECSServiceCreateTimeout(app_name)

        return app_url, lb_arn, target_group_arn, listener_arn

    def delete_listener(self, app_details_obj):
        successfully_deleted = False
        count = 3
        i = 0
        while not successfully_deleted and i < count:
            try:
                self.alb_client.delete_listener(ListenerArn=app_details_obj['listener_arn'])
            except Exception as e:
                fmlogger.error("Exception encountered in deleting listener %s" % e)
                i = i + 1
                time.sleep(2)
            else:
                successfully_deleted = True
        if not successfully_deleted:
            fmlogger.debug("Could not delete ELB listener.")

    def delete_target_group(self, app_details_obj):
        successfully_deleted = False
        count = 3
        i = 0
        while not successfully_deleted and i < count:
            try:
                self.alb_client.delete_target_group(TargetGroupArn=app_details_obj['target_group_arn'])
            except Exception as e:
                fmlogger.error("Exception encountered in deleting target group %s" % e)
                i = i + 1
                time.sleep(2)
            else:
                successfully_deleted = True
        if not successfully_deleted:
            fmlogger.debug("Could not delete ELB target group.")

    def delete_load_balancer(self, app_details_obj):
        successfully_deleted = False
        count = 3
        i = 0
        while not successfully_deleted and i < count:
            try:
                self.alb_client.delete_load_balancer(LoadBalancerArn=app_details_obj['lb_arn'])
            except Exception as e:
                fmlogger.error("Exception encountered in deleting load balancer %s" % e)
                i = i + 1
                time.sleep(2)
            else:
                successfully_deleted = True
        if not successfully_deleted:
            fmlogger.debug("Could not delete ELB loadbalancer.")

    def run_command(self, env_id, env_name, resource_obj, command):
        command_output = ''
        env_obj = env_db.Environment().get(env_id)
        df_dir = env_obj.location

        if not os.path.exists(df_dir):
            mkdir_command = ("mkdir {df_dir}").format(df_dir=df_dir)
            os.system(mkdir_command)

        dockerfile_name = "Dockerfile.run_command"
        df_path = df_dir + "/" + dockerfile_name

        df = self.docker_handler.get_dockerfile_snippet("aws")
        df = df + ("COPY . /src \n"
                   "WORKDIR /src \n"
                   "RUN cp -r aws-creds $HOME/.aws \n"
                   "CMD [\"sh\", \"/src/run_command.sh\"] "
                  )

        df_name = df_dir + "/Dockerfile.run_command"
        fp = open(df_name, "w")
        fp.write(df)
        fp.close()

        fp1 = open(df_dir + "/run_command.sh", "w")
        fp1.write("#!/bin/bash \n")
        fp1.write(command)
        fp1.close()

        resource_name = resource_obj.cloud_resource_id
        cont_name = resource_name + "_run_command"
        err, output = self.docker_handler.build_container_image(
            cont_name,
            df_name,
            df_context=df_dir
        )

        if err:
            error_msg = ("Error encountered in running command {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

        err, output = self.docker_handler.run_container(cont_name)

        if err:
            error_msg = ("Error encountered in running command {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

        cont_id = output.strip()

        err, command_output = self.docker_handler.get_logs(cont_id)

        #self.docker_handler.stop_container(cont_id)
        self.docker_handler.remove_container(cont_id)
        self.docker_handler.remove_container_image(cont_name)
        return command_output

    def resource_type_for_command(self, command):
        resource_type_for_command = {}
        resource_type_for_command["aws ecs"] = 'ecs'
        resource_type_for_command["aws rds"] = 'rds'

        type = ''
        for key, value in resource_type_for_command.iteritems():
            if command.find(key) >= 0:
                type = value

        return type

    def get_attached_policies(self):
        attached_policies_list = []

        resp1 = self.iam_client.get_account_authorization_details()

        user_list = resp1['UserDetailList']
        if user_list:
            user_policy_list = resp1['UserDetailList'][0]['UserPolicyList']
            for policy in user_policy_list:
                #print(policy['PolicyName'])
                attached_policies_list.append(policy['PolicyName'])

            attached_managed_policy_list = resp1['UserDetailList'][0]['AttachedManagedPolicies']
            for policy in attached_managed_policy_list:
                attached_policies_list.append(policy['PolicyName'])

        group_detail_list = resp1['GroupDetailList']
        if group_detail_list:
            group_policy_list = group_detail_list[0]['GroupPolicyList']
            for policy in group_policy_list:
                attached_policies_list.append(policy['PolicyName'])

            attached_managed_policy_list = group_detail_list[0]['AttachedManagedPolicies']
            for policy in attached_managed_policy_list:
                attached_policies_list.append(policy['PolicyName'])

        role_detail_list = resp1['RoleDetailList']
        if role_detail_list:
            for role in role_detail_list:
                role_policy_list = role['RolePolicyList']
                for policy in role_policy_list:
                    attached_policies_list.append(policy['PolicyName'])

                attached_managed_policy_list = role['AttachedManagedPolicies']
                for policy in attached_managed_policy_list:
                    attached_policies_list.append(policy['PolicyName'])

        return attached_policies_list