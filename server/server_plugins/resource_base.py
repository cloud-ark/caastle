import abc

import six


@six.add_metaclass(abc.ABCMeta)
class ResourceBase(object):
    """Base class for CloudARK resources."""

#    def __init__(self, env_definition):
#        self.env_definition = env_definition
        
    def __init__(self):
        pass

    @abc.abstractmethod
    def create(self, env_id, resource_details):
        """Create resource in the environment.

        :param env_id: Id of the environment in which resource is defined.
        :param resource_details: A dictionary containing information that
                                 will be used during resource creation
                                 Includes: type of resource,
                                 resource config defined in env_definition
        """

    @abc.abstractmethod
    def delete(self, resource_obj):
        """Delete resource.

        :param resource_obj: Resource's ORM object handle.
        
        """
