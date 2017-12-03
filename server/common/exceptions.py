import abc

import six


@six.add_metaclass(abc.ABCMeta)
class AppDeploymentValidationFailure(Exception):
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_message(self):
        pass

@six.add_metaclass(abc.ABCMeta)
class AppDeploymentFailure(Exception):
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_message(self):
        pass

@six.add_metaclass(abc.ABCMeta)
class EnvironmentDeleteFailure(Exception):
    def __init__(self, message):
        self.message = ("Deleting environment encountered error: {msg}").format(msg=message)

    @abc.abstractmethod
    def get_message(self):
        return self.message

class ECSServiceCreateTimeout(AppDeploymentFailure):

    def __init__(self, app_name):
        self.message = ("App {app_name} Deployment timeout.").format(app_name=app_name)

    def get_message(self):
        return self.message


class HostPortConflictException(AppDeploymentValidationFailure):

    def __init__(self, host_port):
        self.message = "Host port " + str(host_port) + " is not available."

    def get_message(self):
        return self.message
