Architecture
-------------

CloudARK consists of a server component and a client component. 
The server process is started when cloudark is installed.
It listens on port 5002. The client component connects to the server locally over HTTP.
Users see a command-line interface that hides these details.

There are two main abstractions in CloudARK - *Environment* and *Application*.


.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   environment
   application
