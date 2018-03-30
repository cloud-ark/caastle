CaaStle Architecture
----------------------

CaaStle is implemented as extensible and modular architecture as shown in following diagram:

   .. image:: architecture.jpg
      :scale: 70%


There are two primary architectural components - *client* and *server*.
To offer the non-hosted functionality, both these components run on the same machine.
When CaaStle is installed the client is installed in a Python virtual environment.
The server is started in this virtual environment when start-cloudark.sh script is run.
The client and the server communicate over a REST API locally.

Client is implemented using the cliff_ framework.

.. _cliff: https://docs.openstack.org/cliff/latest/

The server is implemented as an extensible architecture with separate packages for different
clouds. Within each cloud package there are sub-packages for *coe* and *resource*.
These packages contain modules that implement coe-specific and resource-specific functionality
for the target cloud. These modules are implemented as extensions of CaaStle. We use
stevedore_ extension mechanism for this purpose.

.. _stevedore: https://pypi.python.org/pypi/stevedore

The server uses Python threads to asynchronously handle incoming requests. We considered using
a queue-based approach. But because our goal was to create a *non-hosted* implementation, we rejected it for the simpler thread-based approach. Currently CaaStle works with Python 2.7
only as the thread package is available only in Python 2.7. We have an open_ issue for making CaaStle
use concurrency mechanisms available in the latest versions of Python.

.. _open: https://github.com/cloud-ark/cloudark/issues/34

For making calls against cloud endpoints, appropriate authorization credentials are needed. CaaStle provides commands to do the credential setup.
More information about CaaStle's authorization needs is available in the `authorization details`__ section.

.. _auth: https://cloud-ark.github.io/caastle/docs/html/html/cloud_auth.html

__ auth_

We want CaaStle to be at least as reliable as the underlying Cloud. This led us to not use any timeouts
for cloud resource creation actions. After CaaStle initiates a creation call to the cloud, it periodically
reads the status of the resource and updates its internal state. CaaStle terminates this polling only if
the resource becomes available or if the cloud indicates that the resource provisioning has failed. There
are no timeouts within CaaStle around these polling checks.

CaaStle strives to provide atomicity around resource provisioning. As part of provisioning a top-level resource,
other resources are created. For example, when creating a ECS cluster, first appropriate security groups are created and a ssh key pair is created. If cluster creation fails, these resources are deleted thus ensuring
atomicity of cluster create action. Similar approach is used when provisioning of database resources (RDS,
Cloud SQL). 


**Docker as a command execution mechanism**

CaaStle uses combination of target cloud’s SDKs and CLIs as cloud interaction mechanisms.
SDKs have been our first choice as they allow us complete control over interaction steps.
But for cases where SDK was not supporting a particular requirement, we have used corresponding native CLI calls.
For this, we use Docker as the *mechanism for invoking these CLIs*.
We have built `base Docker images`__ containing AWS and Google Cloud CLIs which we use for this purpose.

.. _baseimages: https://hub.docker.com/r/lmecld/clis/tags/

__ baseimages_

We build custom Docker images corresponding to a CLI call. The corresponding Dockerfiles
are stored in application-specific folder inside ~/.cld/data/deployments directory.
This approach has the benefit that there is no need for the user to install cloud CLIs on his/her machine.
In fact, we leverage this same mechanism to support `environment-specific shell`__.

.. _envshell: https://cloud-ark.github.io/caastle/docs/html/html/faq.html

__ envshell_


.. toctree::
   :maxdepth: 1
   
   implementation
   extending   

**Known Issues**

Check this_ for list of currently known issues.

.. _this: https://github.com/cloud-ark/cloudark/issues
