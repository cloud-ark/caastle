Extending CaaStle
-------------------

It is straightforward to extend CaaStle to add new functionality. If you want a new client-side
command, add it in the client folder and hook it up with the rest of the client-side
system by making entry for it in the setup.py client module.

If you want to extend server-side functionality, the key places to look at are:

- fmserver.py: This is the REST entry point for server-side processing.

- server/server_plugins: This is the package corresponding to different target clouds.

- server/setup.py: This is the module where stevedore entrypoints are set.

- server/dbmodule: This package includes CaaStle's state management functionality.

