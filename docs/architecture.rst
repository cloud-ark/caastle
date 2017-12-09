CloudARK Architecture
----------------------

CloudARK is implemented as extensible and modular architecture.
There are two primary architectural components - *client* and *server*.
When CloudARK is installed the client is installed in a Python virtual environment.
The server is started in this virtual environment when start-cloudark.sh script is run.
The client and the server communicate over a REST API.

Client is implemented using the cliff_ framework.

.. _cliff: https://docs.openstack.org/cliff/latest/

The server is implemented as a modular architecture with separate packages for different
clouds. Within each cloud package there are sub-packages for *coe* and *resource*.
These packages contain modules that implement coe-specific and resource-specific functionality
for the cloud target. These modules are implemented as extensions of CloudARK. We use
stevedore_ extension mechanism for this purpose.

.. _stevedore: https://pypi.python.org/pypi/stevedore

The server uses Python threads to asynchronously handle incoming requests. Currently CloudARK works
with Python 2.7 only as the thread package is available only in Python 2.7.
We have an open_ issue for making CloudARK use concurrency mechanisms available in latest versions of Python.

.. _open: https://github.com/cloud-ark/cloudark/issues/34

For making calls against cloud endpoints, appropriate authorization credentials are needed. CloudARK provides commands to do the credential setup.

Actual calls are made either as API requests through the appropriate cloud SDK or using direct native cloud CLIs.
For most of the calls we try to use the native SDK first. But if the SDK is not supporting
any particular call, we resort to using native CLI calls.
When using native CLIs, we use *Docker as the mechanism* for making these CLI calls.
We have built base Docker images containing AWS and Google Cloud CLIs that are used for this purpose.


Extending CloudARK
-------------------

It is straightforward to extend CloudARK to add new functionality. If you need new client-side
command, add it in the client folder and hook it up with the rest of the client-side
system by making entry for it in the setup.py client module.

If you want to extend server-side functionality, the key places to look at are:

- fmserver.py: This is the REST entry point for server-side processing.

- server/server_plugins: This is the package corresponding to different target clouds.

- server/setup.py: This is the module where stevedore entrypoints are set.

- server/dbmoule: This package includes CloudARK's state management functionality.


*Known Issues*

Check this_ for known issues.

.. _this: https://github.com/cloud-ark/cloudark/issues
