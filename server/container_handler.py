import threading

from common import fm_logger

import local_handler

fmlogging = fm_logger.Logging()

try:
    import aws_handler
except Exception as e:
    fmlogging.error("Error occurred in loading aws_handler %s" % str(e))

try:
    import gcloud_handler
except Exception as e:
    fmlogging.error("Error occurred in loading gcloud_handler %s " % str(e))


class ContainerHandler(threading.Thread):

    registered_cloud_handlers = dict()
    registered_cloud_handlers['local'] = local_handler.LocalHandler()

    try:
        registered_cloud_handlers['ecr'] = aws_handler.AWSHandler()
    except Exception as e:
        fmlogging.error(str(e))

    try:
        registered_cloud_handlers['gcr'] = gcloud_handler.GCloudHandler()
    except Exception as e:
        fmlogging.error(str(e))

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
