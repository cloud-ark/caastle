import ast
import os
from os.path import expanduser
import re
import shutil
import time

from kubernetes import client, config

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from google.oauth2 import service_account

from server.common import constants
from server.common import common_functions
from server.common import docker_lib
from server.common import exceptions
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db
import server.server_plugins.coe_base as coe_base
from server.server_plugins.gcloud import gcloud_helper
from __builtin__ import True

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

SERVICE_ACCOUNT_FILE = APP_AND_ENV_STORE_PATH + "gcp-service-account-key.json"

fmlogger = fm_logger.Logging()

GCR = "us.gcr.io"

GCLOUD_ACTION_TIMEOUT = 60

class GKEHandler(coe_base.COEBase):
    """GKE Handler."""

    gcloudhelper = gcloud_helper.GCloudHelper()

    allowed_commands = ["kubectl get*",
                        "kubectl describe*",
                        "kubectl logs*",
                        "kubectl delete*"]

    help_commands = ["kubectl get ",
                     "kubectl describe ",
                     "kubectl logs ",
                     "kubectl delete "]


    def __init__(self):
        #credentials = GoogleCredentials.get_application_default()
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        self.gke_service = discovery.build('container', 'v1',
                                           credentials=credentials)
        self.compute_service = discovery.build('compute', 'v1',
                                               credentials=credentials,
                                               cache_discovery=False)
        self.docker_handler = docker_lib.DockerLib()

        self.app_yaml_def = ''

    def _verify(self, command):
        matched = None
        for pattern in GKEHandler.allowed_commands:
            p = re.compile(pattern, re.IGNORECASE)
            matched = p.match(command)
            if matched:
                return True
        return False

    def _delete_firewall_rule(self, project, cluster_name):
        try:
            self.compute_service.firewalls().delete(
                project=project,
                firewall=cluster_name
            ).execute()
        except Exception as e:
            fmlogger.error(e)

    def _delete_network(self, project, cluster_name):
        try:
            resp = self.compute_service.networks().delete(
                project=project,
                network=cluster_name
            ).execute()
        except Exception as e:
            fmlogger.error(e)

        network_deleted = False
        count = 0
        while not network_deleted and count < GCLOUD_ACTION_TIMEOUT:
            try:
                network_obj = self.compute_service.networks().get(
                    project=project,
                    network=cluster_name
                ).execute()
            except Exception as e:
                fmlogger.error(e)
                network_deleted = True
            else:
                time.sleep(1)
                count = count + 1
 
        if count >= GCLOUD_ACTION_TIMEOUT:
            message = ("Failed to delete network {network_name}").format(network_name=cluster_name)
            raise exceptions.EnvironmentDeleteFailure("Failed to delete network ")

    def _create_firewall_rule(self, env_id, project, cluster_name):
        count = 0
        while count < GCLOUD_ACTION_TIMEOUT:
            try:
                resp = self.compute_service.firewalls().insert(
                    project=project,
                    body={"direction": "INGRESS",
                          "allowed": [{"IPProtocol": "tcp",
                                       "ports": ["80","443"]}],
                          "network": "global/networks/" + cluster_name,
                          "name": cluster_name
                          }
                ).execute()
                break
            except Exception as e:
                fmlogger.error(e)
                time.sleep(2)
                count = count + 1

        if count >= GCLOUD_ACTION_TIMEOUT:
            raise exceptions.AppDeploymentFailure()

    def _create_network(self, env_id, project, cluster_name):
        network_name = cluster_name
        try:
            resp = self.compute_service.networks().insert(
                project=project,
                body={"autoCreateSubnetworks": True,
                      "routingConfig":{
                          "routingMode": "GLOBAL"
                      },
                      "name": network_name
                     }
            ).execute()
        except Exception as e:
            fmlogger.error(e)
            env_update = {}
            env_update['output_config'] = str({'error': str(e)})
            env_db.Environment().update(env_id, env_update)
            raise e
        
        network_obj = ''
        count = 0
        while not network_obj:
            try:
                network_obj = self.compute_service.networks().get(
                    project=project,
                    network=network_name
                ).execute()
            except Exception as e:
                fmlogger.error(e)
                #env_update = {}
                #env_update['output_config'] = str({'error': str(e)})
                #env_db.Environment().update(env_id, env_update)
            
            if network_obj:
                break
            else:
                time.sleep(2)
                count = count + 1
 
        if count >= GCLOUD_ACTION_TIMEOUT:
            raise exceptions.AppDeploymentFailure()

        return network_obj

    def _get_cluster_node_ip(self, env_name, project, zone):
        pageToken = None
        list_of_node_objs = []
        list_of_ips = []

        try:
            resp = self.compute_service.instances().list(
                project=project, zone=zone, orderBy="creationTimestamp desc",
                pageToken=pageToken).execute()

            for res in resp['items']:
                if res['name'].lower().find(env_name) >= 0:
                    list_of_node_objs.append(res)

            for res in list_of_node_objs:
                external_ip = res['networkInterfaces'][0]['accessConfigs'][0]['natIP']
                print(res)
                list_of_ips.append(external_ip.strip())
        except Exception as e:
            fmlogger.error(e)
            raise e

        return list_of_ips

    def create_cluster(self, env_id, env_info):
        fmlogger.debug("Creating GKE cluster.")

        cluster_status = 'unavailable'

        env_obj = env_db.Environment().get(env_id)
        env_name = env_obj.name
        env_details = ast.literal_eval(env_obj.env_definition)

        env_output_config = ast.literal_eval(env_obj.output_config)
        env_version_stamp = env_output_config['env_version_stamp']

        cluster_name = env_name + "-" + env_version_stamp

        filtered_description = {}

        res_data = {}
        res_data['env_id'] = env_id
        res_data['cloud_resource_id'] = cluster_name
        res_data['type'] = 'gke-cluster'
        res_data['status'] = 'provisioning'
        res_id = res_db.Resource().insert(res_data)

        cluster_size = 1
        if 'cluster_size' in env_details['environment']['app_deployment']:
            cluster_size = env_details['environment']['app_deployment']['cluster_size']

        project = ""
        if 'project' in env_details['environment']['app_deployment']:
            project = env_details['environment']['app_deployment']['project']
        else:
            fmlogger("Project ID required. Not continuing with the request.")
            status = 'not-continuing-with-provisioning:missing parameter project id'
            res_data['status'] = status
            res_db.Resource().update(res_id, res_data)
            return status

        zone = ""
        if 'zone' in env_details['environment']['app_deployment']:
            zone = env_details['environment']['app_deployment']['zone']
        else:
            fmlogger("Zone required. Not continuing with the request.")
            status = 'not-continuing-with-provisioning:missing parameter zone'
            res_data['status'] = status
            res_db.Resource().update(res_id, res_data)
            return status

        filtered_description['cluster_name'] = cluster_name
        filtered_description['project'] = project
        filtered_description['zone'] = zone
        filtered_description['env_name'] = env_name
        res_data['filtered_description'] = str(filtered_description)
        res_db.Resource().update(res_id, res_data)

        instance_type = 'n1-standard-1'
        if 'instance_type' in env_details['environment']['app_deployment']:
            instance_type = env_details['environment']['app_deployment']['instance_type']

        network = ''
        if 'network' in env_details['environment']['app_deployment']:
            network = env_details['environment']['app_deployment']['network']
        if not network or network != 'default':
            network = cluster_name
            try:
                self._create_network(env_id, project, cluster_name)
            except Exception as e:
                fmlogger.error(e)
                return

            try:
                self._create_firewall_rule(env_id, project, cluster_name)
            except Exception as e:
                fmlogger.error(e)
                return

        resp = ''
        try:
            resp = self.gke_service.projects().zones().clusters().create(
                projectId=project,
                zone=zone,
                body={"cluster": {"name": cluster_name,
                                  "initialNodeCount": cluster_size,
                                  "nodeConfig": {
                                      "oauthScopes": "https://www.googleapis.com/auth/devstorage.read_only",
                                      "machineType": instance_type},
                                  "network": network}}
            ).execute()
            fmlogger.debug(resp)
        except Exception as e:
            fmlogger.error(e)

            env_update = {}
            env_update['output_config'] = str({'error': str(e)})
            env_db.Environment().update(env_id, env_update)
            # Cleanup
            self._delete_firewall_rule(project, cluster_name)
            return

        count = 1
        available = False
        while not available:
            resp = self.gke_service.projects().zones().clusters().get(
                projectId=project,
                zone=zone,
                clusterId=cluster_name).execute()
            status = resp['status']
            res_data['status'] = status
            res_db.Resource().update(res_id, res_data)
            if status.lower() == 'running' or status.lower() == 'available':
                available = True
                break
            else:
                count = count + 1
                time.sleep(3)

        instance_ip_list = ''
        try:
            instance_ip_list = self._get_cluster_node_ip(env_name,
                                                         project,
                                                         zone)
        except Exception as e:
            cluster_status = 'unavailable ' + str(e)
        else:
            cluster_status = 'available'

        if instance_ip_list:
            env_output_config['cluster_ips'] = instance_ip_list
            env_data = {}
            env_data['output_config'] = str(env_output_config)
            env_db.Environment().update(env_id, env_data)
            res_data['status'] = cluster_status
            filtered_description['cluster_ips'] = instance_ip_list
            res_data['filtered_description'] = str(filtered_description)
            res_db.Resource().update(res_id, res_data)
            fmlogger.debug("Done creating GKE cluster.")
        else:
            resource_obj = res_db.Resource().get(res_id)
            cluster_status = 'Could not get IP address of the cluster.. Not continuing.. Deleting cluster.'
            res_data['status'] = cluster_status
            res_db.Resource().update(res_id, res_data)
            self.delete_cluster(env_id, env_info, resource_obj)
            fmlogger.debug("Done deleting GKE cluster.")
        return cluster_status

    def delete_cluster(self, env_id, env_info, resource_obj):
        fmlogger.debug("Deleting GKE cluster")

        res_db.Resource().update(resource_obj.id, {'status': 'deleting'})
        try:
            filtered_description = ast.literal_eval(resource_obj.filtered_description)
            cluster_name = filtered_description['cluster_name']
            project = filtered_description['project']
            zone = filtered_description['zone']

            env_obj = env_db.Environment().get(env_id)
            env_name = env_obj.name
            env_details = ast.literal_eval(env_obj.env_definition)

            network = ''
            if 'network' in env_details['environment']['app_deployment']:
                network = env_details['environment']['app_deployment']['network']
            if not network or network != 'default':
                # Network delete is not working for some reason. So temporarily
                # commenting it out.
                #try:
                #    self._delete_network(project, cluster_name)
                #except Exception as e:
                #    fmlogger.error("Exception deleting network %s " % str(e))
                #    env_update = {}
                #    env_update['output_config'] = str({'error': str(e)})
                #    env_db.Environment().update(env_id, env_update)

                self._delete_firewall_rule(project, cluster_name)

            try:
                resp = self.gke_service.projects().zones().clusters().delete(
                    projectId=project,
                    zone=zone,
                    clusterId=cluster_name
                ).execute()
                fmlogger.debug(resp)
            except Exception as e:
                fmlogger.error("Encountered exception when deleting cluster %s" % e)

            available = True
            while available:
                try:
                    resp = self.gke_service.projects().zones().clusters().get(
                        projectId=project,
                        zone=zone,
                        clusterId=cluster_name).execute()
                except Exception as e:
                    fmlogger.error("Exception encountered in retrieving cluster. Cluster does not exist. %s " % e)
                    available = False
                    break
                time.sleep(3)
        except Exception as e:
            fmlogger.error(e)

        res_db.Resource().delete(resource_obj.id)
        fmlogger.debug("Done deleting GKE cluster.")

    def run_command(self, env_id, env_name, resource_obj, command):
        fmlogger.debug("Running command against GKE cluster")

        if command.lower() == 'help':
            return GKEHandler.help_commands

        command_output = ''

        is_supported_command = self._verify(command)
        if not is_supported_command:
            command_output = ["Command not supported"]
            return command_output

        base_command = ''
        cluster_name = resource_obj.cloud_resource_id

        user_account, project_name, zone_name = GKEHandler.gcloudhelper.get_deployment_details(env_id)

        base_command = ("RUN /google-cloud-sdk/bin/gcloud container clusters get-credentials {cluster_name} --zone {zone} \n").format(
                        cluster_name=cluster_name, zone=zone_name)

        base_image = "gke"
        command_output = GKEHandler.gcloudhelper.run_command(env_id,
                                                             env_name,
                                                             resource_obj,
                                                             base_command,
                                                             command,
                                                             base_image)

        output_lines = command_output.split("\n")

        return output_lines

    # Leaving these methods here as this coe_base.COEBase still contains these methods.
    # Once we remove them from coe_base.COEBase, we should remove these methods
    def deploy_application(self, app_id, app_info):
        pass

    def redeploy_application(self, app_id, app_info):
        pass

    def delete_application(self, app_id, app_info):
        pass

    def get_logs(self, app_id, app_info):
        pass