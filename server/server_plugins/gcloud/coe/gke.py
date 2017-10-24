import ast
import base64
import boto3
import os
from os.path import expanduser
import shutil
import time

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

import server.server_plugins.coe_base as coe_base
from server.common import common_functions
from server.common import constants
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import app as app_db
from server.dbmodule.objects import environment as env_db
from server.dbmodule.objects import resource as res_db

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()


class GKEHandler(coe_base.COEBase):
    """GKE Handler."""
    
    def __init__(self):
        credentials = GoogleCredentials.get_application_default()
        self.gke_service = discovery.build('container', 'v1',
                                           credentials=credentials)
        self.compute_service = discovery.build('compute', 'v1',
                                               credentials=credentials,
                                               cache_discovery=False)

    def _get_cluster_node_ip(self, env_name, project, zone):
        pageToken = None
        list_of_node_objs = []
        list_of_ips = []
        done = False

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

        resp = self.gke_service.projects().zones().clusters().create(
                projectId=project,
                zone=zone,
                body={"cluster":{"name": cluster_name,
                                 "initialNodeCount": cluster_size,
                                 "nodeConfig": {
                                     "oauthScopes": "https://www.googleapis.com/auth/devstorage.read_only"}}}
            ).execute()
    
        fmlogger.debug(resp)

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
                time.sleep(3)

        instance_ip_list = self._get_cluster_node_ip(env_name,
                                                     project,
                                                     zone)

        cluster_status = 'available'
        env_output_config['cluster_ips'] = instance_ip_list
        env_data = {}
        env_data['output_config'] = str(env_output_config)
        env_db.Environment().update(env_id, env_data)
        res_data['status'] = cluster_status
        res_data['filtered_description'] = str({'cluster_ips': instance_ip_list})
        res_db.Resource().update(res_id, res_data)
        fmlogger.debug("Done creating GKE cluster.")
        return cluster_status
        
    def delete_cluster(self, env_id, env_info, resource_obj):
        pass

    def deploy_application(self, app_id, app_info):
        pass

    def redeploy_application(self, app_id, app_info):
        pass

    def delete_application(self, app_id, app_info):
        pass