CloudARK CLI
-------------

.. code:: bash

   (cloudark-virtenv) cld --help
   usage: cld [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

   Platform-as-Code tool for full-stack microservices development for public clouds.

   optional arguments:
     --version            show program's version number and exit
     -v, --verbose        Increase verbosity of output. Can be repeated.
     -q, --quiet          Suppress output except warnings and errors.
     --log-file LOG_FILE  Specify a file to log output. Disabled by default.
     -h, --help           Show help message and exit.
     --debug              Show tracebacks on errors.

   Commands:
     app delete: Delete application

     app deploy: Deploy application in an environment using specified app yaml file

     app list: Show all applications in the system

     app logs: Retrieve application logs

     app show: Show application details

     container create: Create container to be stored in a target repository ('local', 'ecr', 'gcr')

     container delete: Delete container

     container list: Show all containers in the system

     container show: Show container details

     env create: Create environment using specified environment yaml file

     env delete: Delete environment

     env exec: Run the specified cloud-native cli command in the environment

     env list: Show all environments in the system

     env shell: Start an environment-specific shell to run cloud-native cli commands interactively

     env show: Show environment details

     resource list: Show all resources in the system

     resource show: Show resources for an environment

     setup aws:      Set up aws

     setup gcloud:   Set up gcloud
