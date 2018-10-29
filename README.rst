=========
CaaStle
=========

CaaStle is a **full-stack microservices deployment tool** for Google Kubernetes Engine (GKE) and Amazon ECS.

Platform of containerized applications/microservices includes application/web servers, container orchestration engine clusters, and application’s external resource dependencies such as managed database servers.

.. image:: ./docs/screenshots/Block-diagram-short.png
   :scale: 75%
   :align: center


Key elements of CaaStle

- **Application-centric abstractions**:

  *Environment* is the top level abstraction. It defines container orchestration engine cluster and managed cloud services needed by the application.
  *Application* is composed of one or more application containers and is deployed in the environment.
  You get a shell customized for the environment with ability to directly use cloud-native CLIs against the platform elements created in that environment.

- **Declarative platform definition**:

  *environment yaml* file is used to define managed cloud resources within an environment; *application yaml* is used to define application
  container (for single container applications);
  *pod/deployment yaml or ecs's task yaml* is supported for multi-container applications.
  No need for platform inputs using command line parameters.

- **Platform element association**:

  Integrated creation and binding of cloud resources with application containers provides view of the entire application run-time environment with
  appropriate platform elements associations.

- **Environment change history**:

  History of operations that change the state of an environment is maintained for traceability and repeatability.

- **Non-hosted implementation**:

  CaaStle is a non-hosted implementation. There is no centralized server like PaaS implementations. CaaStle can be installed anywhere alongside Docker.
  This architecture enables effective local development with Docker environments setup on the individual workstations or laptops.
  The non-hosted nature also simplifies integration of CaaStle with any DevOps workflow.


Read this_ for more details about CaaStle

.. _this: https://cloud-ark.github.io/caastle/docs/html/html/index.html

CaaStle FAQ_

.. _FAQ: https://cloud-ark.github.io/caastle/docs/html/html/faq.html

CaaStle Roadmap_

.. _Roadmap: https://cloud-ark.github.io/caastle/docs/html/html/roadmap.html



Try CaaStle
-------------

Developed and Tested on:

- Ubuntu 14.04, 16.04

- Mac OS (El Capitan 10.11.4)

Requires:

- Docker 1.6 and above

- Python 2.7

CaaStle requires Docker to be installed. If you do not have Docker, you can install it following steps from:

https://docs.docker.com/engine/installation/

On Mac OS, make sure the command shell from which you are installing CaaStle is able to run docker commands
without sudo. You can achieve this by executing following command in the shell once Docker VM is up and running:

eval "$(docker-machine env default)"


Once you have installed Docker follow these steps:


1) Clone this repository

2) Install CaaStle

   $ ./install.sh

3) Do cloud setup

   $ cld setup aws

   $ cld setup gcloud

4) Start CaaStle server

   $ ./start-caastle.sh

5) Choose a sample application from examples folder and follow the steps in the included README


Sample commands
----------------

$ cld --help

usage: cld [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

CloudARK command-line tool to create and manage cloud environments for
containerized applications.

Commands:

  env create

  env list

  env show

  env exec

  env shell

  env delete

  container create

  container list

  container show

  container delete

  app deploy

  app list

  app show

  app logs

  app delete

  setup aws

  setup gcloud



Deployment Examples:
--------------------

1) `Deploying on Google GKE`__

.. _GKE: https://cloud-ark.github.io/caastle/docs/html/html/deployments.html#deployment-to-gke

__ GKE_


2) `Deploying on Amazon ECS`__

.. _ECS: https://cloud-ark.github.io/caastle/docs/html/html/deployments.html#deployment-to-amazon-ecs

__ ECS_




Demo Videos:
------------

1) CaaStle setup: https://youtu.be/88kClIy8qp4

2) Wordpress deployment on GKE: https://youtu.be/c7pO7TO0KzU

3) Wordpress deployment on ECS: https://youtu.be/psgFyCa2PQA


Wordpress deployment on ECS
---------------------------

1) Environment definition

   .. image:: ./docs/screenshots/wordpress/env-yaml.png

2) Create environment
   
   $ cld env create wpenv environment-rds-ecs.yaml
 
   .. image:: ./docs/screenshots/wordpress/env-create.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/env-show-available.png
      :scale: 125%

3) Create application container

   $ cld container create wordpresscont ecr
 
   .. image:: ./docs/screenshots/wordpress/container-create.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/container-ready.png
      :scale: 125%

4) Deploy application

   $ cld app deploy wordpressapp wpenv app-ecs.yaml

   .. image:: ./docs/screenshots/wordpress/app-yaml.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/app-create.png
      :scale: 125%

5) Check application status

   $ cld app show wordpressapp

   .. image:: ./docs/screenshots/wordpress/app-deployment-done.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/app-logs.png
      :scale: 125%

6) Wordpress deployment complete

   .. image:: ./docs/screenshots/wordpress/wordpress-installed.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/wordpress-blog-page-with-elb.png
      :scale: 125%

7) AWS console

   .. image:: ./docs/screenshots/wordpress/wordpress-rds-instance.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/wordpress-task-definition.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/wordpress-container.png
      :scale: 125%


Issues
=======

Suggestions/Issues are welcome_.

.. _welcome: https://github.com/cloud-ark/caastle/issues