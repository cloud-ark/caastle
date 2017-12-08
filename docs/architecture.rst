Under the Hood
--------------

CloudARK is implemented as extensible and modular architecture.
There are two primary architectural components - *client* and *server*.
When CloudARK is installed the client is installed in a Python virtual environment.
The server is started in this virtual environment when the start-cloudark.sh script is run.

Client is implemented using the cliff_ framework.

.. _cliff: https://docs.openstack.org/cliff/latest/

The server is implemented as a modular architecture with separate packages for different
clouds. Within each cloud package there are sub-packages for *coe* and *resource*.
These packages are home for implementing coe-specific functionality and resource-specific functionality
for that cloud. These modules are implemented using the stevedore_ extension mechanism.

.. _stevedore: https://pypi.python.org/pypi/stevedore

The Server-side uses Python threads to asynchronously handle incoming requests. Note that currently the thread
package is available only in Python 2.7. We have an open_ issue for making CloudARK align with
concurrency facilities available in latest versions of Python.

.. _open: https://github.com/cloud-ark/cloudark/issues/34

For making calls against cloud endpoints, appropriate authorization credentials are needed.
CloudARK provides commands to do the credential setup for Google cloud and AWS.

Actual calls are made either as API requests through the appropriate SDK or direct CLI calls.
For most of the calls we try to use native SDK first. But if the SDK is not supporting
any particular call, we resort to using direct CLI calls.
For using CLI we use Docker as the mechanism for making these CLI calls.
We have base Docker images for AWS and Google CLIs that are used for this purpose.


Extending CloudARK
-------------------

Its easy to extend CloudARK to add new functionality. If you need new client-side
command, add it in the client folder and hook it up with the rest of the client-side
system by making entry for it in the setup.py client module.

If you want to extend server-side functionality then the key places to look at are:

- fmserver.py: This is the entry point for server-side processing

- server/server_plugins: This is the package for different cloud targets

- server/dbmoule: This package includes CloudARK's state management functionality

- server/setup.py: This is the file for setting up stevedore entrypoints


