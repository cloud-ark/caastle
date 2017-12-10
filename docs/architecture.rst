CloudARK Architecture
----------------------

CloudARK is implemented as extensible and modular architecture.
There are two primary architectural components - *client* and *server*.
When CloudARK is installed the client is installed in a Python virtual environment.
The server is started in this virtual environment when start-cloudark.sh script is run.
The client and the server communicate over a REST API.

Client is implemented using the cliff_ framework.

.. _cliff: https://docs.openstack.org/cliff/latest/

The server is implemented as a extensible architecture with separate packages for different
clouds. Within each cloud package there are sub-packages for *coe* and *resource*.
These packages contain modules that implement coe-specific and resource-specific functionality
for the target cloud. These modules are implemented as extensions of CloudARK. We use
stevedore_ extension mechanism for this purpose.

.. _stevedore: https://pypi.python.org/pypi/stevedore

The server uses Python threads to asynchronously handle incoming requests. Currently CloudARK works
with Python 2.7 only as the thread package is available only in Python 2.7.
We have an open_ issue for making CloudARK use concurrency mechanisms available in latest versions of Python.

.. _open: https://github.com/cloud-ark/cloudark/issues/34

For making calls against cloud endpoints, appropriate authorization credentials are needed. CloudARK provides commands to do the credential setup.
More information about CloudARK's authorization needs is available in the `authorization details`__ section.

.. _auth: https://cloud-ark.github.io/cloudark/docs/html/html/deployments.html#authorization-details

__ auth_

**Docker as a command execution mechanism**

CloudARK uses combination of target cloud’s SDKs and CLIs as cloud interaction mechanisms.
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

.. _envshell: https://cloud-ark.github.io/cloudark/docs/html/html/faq.html

__ envshell_



Extending CloudARK
-------------------

It is straightforward to extend CloudARK to add new functionality. If you want a new client-side
command, add it in the client folder and hook it up with the rest of the client-side
system by making entry for it in the setup.py client module.

If you want to extend server-side functionality, the key places to look at are:

- fmserver.py: This is the REST entry point for server-side processing.

- server/server_plugins: This is the package corresponding to different target clouds.

- server/setup.py: This is the module where stevedore entrypoints are set.

- server/dbmodule: This package includes CloudARK's state management functionality.


**Known Issues**

Check this_ for list of currently known issues.

.. _this: https://github.com/cloud-ark/cloudark/issues
