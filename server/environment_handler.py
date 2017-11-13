import threading

import aws_handler
import gcloud_handler
import local_handler
from common import fm_logger
from dbmodule.objects import environment as env_db
from dbmodule.objects import resource as res_db

fmlogging = fm_logger.Logging()


class EnvironmentHandler(threading.Thread):

    registered_cloud_handlers = dict()
    registered_cloud_handlers['aws'] = aws_handler.AWSHandler()
    registered_cloud_handlers['gcloud'] = gcloud_handler.GCloudHandler()
    registered_cloud_handlers['local'] = local_handler.LocalHandler()

    def __init__(self, env_id, environment_def, environment_info, action=''):
        self.env_id = env_id
        self.environment_def = environment_def
        self.environment_info = environment_info
        self.action = action

    def _create_environment(self):
        """Create environment.

        environment:
           resources:
              aws:
                - resource:
                    type: rds
                    configuration:
                      engine: mysql
                      flavor: db.m1.medium
                      policy:
                        access: open
                - resource:
                    type: container
                    name: nginx
                    source: https://hub.docker.com/_/nginx/
            app_deployment:
              target: aws
              type: ecs
        """
        if not self.environment_def:
            fmlogging.debug("Environment definition is empty. Cannot create empty environment. Returning.")
            return

        env_details = self.environment_def['environment']

        status_list = []
        # First create ECS resources (cluster)
        if 'app_deployment' in env_details:
            app_deployment = env_details['app_deployment']
            if app_deployment['target'] == 'aws':
                env_db.Environment().update(self.env_id, {'status': 'creating_ecs_cluster'})
                status = EnvironmentHandler.registered_cloud_handlers['aws'].create_cluster(self.env_id,
                                                                                            self.environment_info)
                status_list.append(status)
            if app_deployment['target'] == 'gcloud':
                env_db.Environment().update(self.env_id, {'status': 'creating_gke_cluster'})
                status = EnvironmentHandler.registered_cloud_handlers['gcloud'].create_cluster(self.env_id,
                                                                                               self.environment_info)
                status_list.append(status)

        # Then create other resources (as we want to set security-groups of other resources to
        # match does of the ECS cluster.
        if 'resources' in env_details:
            resources = env_details['resources']
            resources_list = ''
            if 'aws' in resources:
                fmlogging.debug("Creating AWS resources")
                resources_list = resources['aws']
                stat_list = EnvironmentHandler.registered_cloud_handlers['aws'].create_resources(self.env_id, resources_list)
                status_list.extend(stat_list)
            if 'gcloud' in resources:
                fmlogging.debug("Creating Google resources")
                resources_list = resources['gcloud']
                stat_list = EnvironmentHandler.registered_cloud_handlers['gcloud'].create_resources(self.env_id, resources_list)
                status_list.extend(stat_list)

        all_available = True
        for stat in status_list:
            if stat == 'available':
                all_available = all_available and True
            else:
                all_available = all_available and False
        
        if all_available:
            env_db.Environment().update(self.env_id, {'status': 'available'})
        else:
            fmlogging.debug("One or more resources in environment failed to provision.")

    def _delete_environment(self):
        env_db.Environment().update(self.env_id, {'status': 'deleting'})

        resource_list = res_db.Resource().get_resources_for_env(self.env_id)
        for resource in resource_list:
            type = resource.type
            if type == 'ecs-cluster':
                EnvironmentHandler.registered_cloud_handlers['aws'].delete_cluster(self.env_id,
                                                                                   self.environment_info,
                                                                                   resource)
            if type == 'gke-cluster':
                EnvironmentHandler.registered_cloud_handlers['gcloud'].delete_cluster(self.env_id,
                                                                                      self.environment_info,
                                                                                      resource)
            if type in ['rds']:
                EnvironmentHandler.registered_cloud_handlers['aws'].delete_resource(self.env_id,
                                                                                    resource)
            if type in ['cloudsql']:
                EnvironmentHandler.registered_cloud_handlers['gcloud'].delete_resource(self.env_id,
                                                                                       resource)

        env_db.Environment().delete(self.env_id)

    def run(self):
        if self.action == 'create':
            fmlogging.debug("Creating environment with id %s " % self.env_id)
            self._create_environment()
        if self.action == 'delete':
            fmlogging.debug("Deleting environment with id %s " % self.env_id)
            self._delete_environment()
