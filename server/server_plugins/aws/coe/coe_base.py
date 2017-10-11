import abc

import six


@six.add_metaclass(abc.ABCMeta)
class COEBase(object):
    """Base class for CloudARK container clusters and containers.
    """

    @abc.abstractmethod
    def create_cluster(self, env_id, env_info):
        """Create cluster in the environment.

        :param env_id: DB Id of the environment in which cluster is defined.
        :param env_info: A dictionary containing information that
                         will be used during cluster creation
                         Includes: type of resource,
                         resource config defined in env_definition
        """

    @abc.abstractmethod
    def delete_cluster(self, env_id, env_info, resource_obj):
        """Delete cluster.

        :param env_id: DB Id of the environment in which cluster is defined.
        :param env_info: A dictionary containing information that
                         will be used during cluster creation
                         Includes: type of resource,
                         resource config defined in env_definition
        :param resource_obj: Resource's ORM object handle.
        
        """

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
        """Deploy application.

        :param app_id: DB Id of the application.
        :param app_info: A dictionary containing information that
                         will be used during application creation
                         Includes: env_id, location of Dockerfile, etc.
        """

    @abc.abstractmethod
    def delete_application(self, app_id, app_info):
        """Deploy application.

        :param app_id: DB Id of the application.
        :param app_info: A dictionary containing information that
                         will be used during application creation
                         Includes: env_id, location of Dockerfile, etc.
        """
