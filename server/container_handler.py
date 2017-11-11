import threading

import aws_handler
from common import fm_logger
import gcloud_handler
import local_handler

fmlogging = fm_logger.Logging()


class ContainerHandler(threading.Thread):

    registered_cloud_handlers = dict()
    registered_cloud_handlers['ecr'] = aws_handler.AWSHandler()
    registered_cloud_handlers['gcr'] = gcloud_handler.GCloudHandler()
    
    def __init__(self, cont_name, cont_info, action=''):
        self.cont_name = cont_name
        self.cont_info = cont_info
        self.action = action

    def _create_cont(self):
        if not self.cont_info:
            fmlogging.debug("Container information is empty. Returning.")
            return
        cloud = self.cont_info['dep_target']
        ContainerHandler.registered_cloud_handlers[cloud].create_container(self.cont_name, self.cont_info)

    def _delete_cont(self):
        if not self.cont_info:
            fmlogging.debug("Container information is empty. Returning.")
            return
        cloud = self.cont_info['dep_target']
        ContainerHandler.registered_cloud_handlers[cloud].delete_container(self.cont_name, self.cont_info)

    def run(self):
        fmlogging.debug("Handling request for container name %s " % self.cont_name)
        if self.action == 'create':
            self._create_cont()
        if self.action == 'delete':
            self._delete_cont()
