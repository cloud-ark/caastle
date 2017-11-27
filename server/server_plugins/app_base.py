import abc

import six


@six.add_metaclass(abc.ABCMeta)
class AppBase(object):
    """Base class for CloudARK app deployments. """

    @abc.abstractmethod
    def deploy_application(self, app_id, app_info):
        """Deploy application.

        :param app_id: DB Id of the application.
        :param app_info: A dictionary containing information that
                         will be used during application creation
                         Includes: env_id, location of Dockerfile, etc.
        """

    @abc.abstractmethod
    def redeploy_application(self, app_id, app_info):
        """Redeploy application.

        :param app_id: DB Id of the application.
        :param app_info: A dictionary containing information that
                         was used during application creation
                         Includes: env_id, location of Dockerfile, etc.
        """

    @abc.abstractmethod
    def delete_application(self, app_id, app_info):
        """Delete application.

        :param app_id: DB Id of the application.
        :param app_info: A dictionary containing information that
                         was used during application creation
                         Includes: env_id, location of Dockerfile, etc.
        """

    @abc.abstractmethod
    def get_logs(self, app_id, app_info):
        """Retrieve logs for application.

        :param app_id: DB Id of the application.
        :param app_info: A dictionary containing information that
                         was used during application creation
                         Includes: env_id, location of Dockerfile, etc.
        """
