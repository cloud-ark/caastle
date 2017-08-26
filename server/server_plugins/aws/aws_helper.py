import ast
import base64
import boto3
import json
import os
import shutil
import time

from common import constants
from common import fm_logger
from dbmodule import db_handler
from common import docker_lib

fmlogger = fm_logger.Logging()
dbhandler = db_handler.DBHandler()

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
        
        fmlogger.debug("lb target group creation done. target_group_arn:%s target_group_name:%s" % (target_group_arn, target_group_name))
        return target_group_arn, target_group_name

    def _create_lb_listener(self, load_balancer_arn, target_group_arn):
        fmlogger.debug("Creating lb listener.")
        listener_arn = ''
        try:
            response = self.alb_client.create_listener(LoadBalancerArn=load_balancer_arn,
                                                       Protocol='HTTP',
                                                       Port=80,
                                                       DefaultActions=[{'Type':'forward',
                                                                        'TargetGroupArn': target_group_arn}])
            listener_arn = response['Listeners'][0]['ListenerArn']
        except Exception as e:
            fmlogger.error("Encountered exception in creating a lb listener %s" % e)

        fmlogger.debug("Done creating lb listener.")
        return listener_arn

    def get_vpc_details(self, search_key='default'):
        vpc_id = ''
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
        
        vpc_details = {}
        vpc_details['vpc_id'] = vpc_id
        vpc_details['cidr_block'] = cidr_block

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
        
        response = self.ec2_client.describe_subnets()
        subnet_list = response['Subnets']
        for subnet in subnet_list:
            if subnet['VpcId'] == vpc_id:
                subnet_ids.append(subnet['SubnetId'])

        return subnet_ids
    
    def create_security_group_for_vpc(self, vpc_id, group_name):
        fmlogger.debug("Creating security group %s for vpc %s" % (group_name, vpc_id))
        response = self.ec2_client.create_security_group(Description=group_name,
                                                         GroupName=group_name,
                                                         VpcId=vpc_id)
        
        security_group_id = response['GroupId']
        return security_group_id

    def delete_security_group_for_vpc(self, vpc_id, group_id, group_name):
        fmlogger.debug("Deleting security group %s for vpc %s" % (group_name, vpc_id))
        response = self.ec2_client.delete_security_group(GroupId=group_id, GroupName=group_name)
    
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
            response = self.ec2_client.authorize_security_group_ingress(GroupId=group_id,
                                                                        GroupName=group_name,
                                                                        IpPermissions=[{'FromPort':0,
                                                                                        'ToPort':to_port,
                                                                                        'IpRanges':[{'CidrIp':ip_range}],
                                                                                        'IpProtocol':protocol}])
        except Exception as e:
            fmlogger.debug("Encountered exception in adding rule to security group:%s" % e)
        return

    def get_container_port_from_taskdef(self, task_def_arn):
        container_port = 0
        try:
            response = self.ecs_client.describe_task_definition(taskDefinition=task_def_arn)
            container_port = response['taskDefinition']['containerDefinitions'][0]['portMappings'][0]['containerPort']
        except Exception as e:
            fmlogger.error("Encountered exception in describing task definition")
        return int(container_port)

    def update_service(self, app_name, cluster_name, task_def_arn, task_desired_count):
        try:
            response = self.ecs_client.update_service(cluster=cluster_name,
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
                task_arn = tasks['taskArns'][0] # assuming one task current
                try:
                    resp = self.ecs_client.stop_task(cluster=cluster_name, task=task_arn)
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

    def create_service(self, app_name, app_port, vpc_id, subnet_list, sec_group_id, 
                       cluster_name, task_def_arn, container_name):

        app_url = ''
        fmlogger.debug("Creating ECS service for app %s" % app_name)
        sec_group_list = [sec_group_id]
        lb_arn, lb_dns = self._create_application_lb(app_name, subnet_list, sec_group_list)
        target_group_arn, target_group_name = self._create_target_group(app_name, app_port, vpc_id)
        listener_arn = self._create_lb_listener(lb_arn, target_group_arn)
        desired_count = 1 # Number of tasks default to 1

        role_obj = self.iam_client.get_role(RoleName='EcsServiceRole')
        role_arn = role_obj['Role']['Arn']

        try:
            response = self.ecs_client.create_service(cluster=cluster_name,
                                                      serviceName=app_name,
                                                      taskDefinition=task_def_arn,
                                                      loadBalancers=[{'targetGroupArn': target_group_arn,
                                                                      #'loadBalancerName': app_name,
                                                                      'containerName': container_name,
                                                                      'containerPort': int(app_port)}],
                                                      desiredCount=desired_count,
                                                      role=role_arn)
        except Exception as e:
            fmlogger.debug("Exception encountered in creating ECS service for app %s" % e)
            return
        fmlogger.debug("ECS service creation for app %s done." % app_name)

        service_available = False
        issue_encountered = False
        service_desc = ''
        while not service_available and not issue_encountered:
            try:
                service_desc = self.ecs_client.describe_services(cluster=cluster_name,
                                                                 services=[app_name])
                pending_count = service_desc['services'][0]['pendingCount']
                running_count = service_desc['services'][0]['runningCount']
                if pending_count == 0 and running_count == desired_count:
                    service_available = True
                    app_url = lb_dns
            except Exception as e:
                fmlogger.debug("Exception encountered in trying to run describe_services. %s" % e)
                issue_encountered = True

        return app_url, lb_arn, target_group_arn, listener_arn