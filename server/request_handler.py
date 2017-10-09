import threading

from common import fm_logger

from server.server_plugins.aws.resource import dynamodb_handler
from server.server_plugins.aws.resource import rds_handler

fmlogging = fm_logger.Logging()


class RequestHandler(threading.Thread):

    registered_services = dict()
    registered_services['rds'] = rds_handler.RDSResourceHandler()
    registered_services['dynamodb'] = dynamodb_handler.DynamoDBResourceHandler()

    def __init__(self, request_obj):
        self.request_obj = request_obj
        self.artifact_type = request_obj['artifact_type']
        self.action = request_obj['action']
        self.resource_type = request_obj['resource_type']

    def _perform_resource_actions(self):
        if self.action == 'create':
            RequestHandler.registered_services[self.resource_type].create(self.request_obj)
        if self.action == 'delete':
            RequestHandler.registered_services[self.resource_type].delete(self.request_obj)

    def run(self):
        fmlogging.debug("Handling %s for %s " % (self.action, self.resource_type))
        if self.artifact_type == 'resource':
            self._perform_resource_actions()
        else:
            fmlogging.error("Incorrect action")
