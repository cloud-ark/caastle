import threading

import aws_handler
from common import fm_logger
import gcloud_handler
import local_handler

from server.dbmodule.objects import app as app_db

fmlogging = fm_logger.Logging()


class AppHandler(threading.Thread):

    registered_cloud_handlers = dict()
    registered_cloud_handlers['aws'] = aws_handler.AWSHandler()
    registered_cloud_handlers['gcloud'] = gcloud_handler.GCloudHandler()
    registered_cloud_handlers['local'] = local_handler.LocalHandler()

    def __init__(self, app_id, app_info, action=''):
        self.app_id = app_id
        self.app_info = app_info
        self.action = action

    def _deploy_app(self):
        if not self.app_info:
            fmlogging.debug("Application information is empty. Cannot deploy application. Returning.")
            return

        cloud = self.app_info['target']
        if cloud == 'aws':
            AppHandler.registered_cloud_handlers['aws'].deploy_application(self.app_id, self.app_info)
        elif cloud == 'gcloud':
            AppHandler.registered_cloud_handlers['gcloud'].deploy_application(self.app_id, self.app_info)
        elif cloud == 'local':
            AppHandler.registered_cloud_handlers['local'].deploy_application(self.app_id, self.app_info)
        else:
            fmlogging.error("Unknown deployment target %s" % cloud)
            return

    def _redeploy_app(self):
        if not self.app_info:
            fmlogging.debug("Application information is empty. Cannot deploy application. Returning.")
            return

        cloud = self.app_info['target']
        if cloud == 'aws':
            AppHandler.registered_cloud_handlers['aws'].redeploy_application(self.app_id, self.app_info)
        elif cloud == 'local':
            AppHandler.registered_cloud_handlers['local'].deploy_application(self.app_id, self.app_info)
        else:
            fmlogging.error("Unknown deployment target %s" % cloud)
            return

    def _delete_app(self):
        cloud = self.app_info['target']
        if cloud == 'aws':
            AppHandler.registered_cloud_handlers['aws'].delete_application(self.app_id, self.app_info)
        elif cloud == 'gcloud':
            AppHandler.registered_cloud_handlers['gcloud'].delete_application(self.app_id, self.app_info)
        elif cloud == 'local':
            AppHandler.registered_cloud_handlers['local'].delete_application(self.app_id, self.app_info)
        else:
            fmlogging.error("Unknown deployment target %s" % cloud)
            app_db.App().delete(self.app_id)
            return

    def run(self):
        fmlogging.debug("Handling request for application id %s " % self.app_id)
        if self.action == 'deploy':
            self._deploy_app()
        if self.action == 'redeploy':
            self._redeploy_app()
        if self.action == 'delete':
            self._delete_app()
