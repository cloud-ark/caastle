=================
CloudARK
=================
CloudARK makes your containerized applications *cloud ready*.

Today, deploying containerized applications on public clouds involves following steps:

1) Provisioning cloud services (such as Amazon RDS)
2) Provisioning container orchestration engine (COE) cluster (such as Amazon ECS or GKE)
3) Building application containers
4) Binding containers to cloud services
5) Deploying containers on COE cluster

Different tools are required for each of these steps currently.

CloudARK is a command-line tool that unifies all these steps and provides a unified experience for
deploying your containerized applications on public clouds.


Try CloudARK
-------------
1) Clone this repository

2) Install CloudARK:

     ./install.sh

3) Clone the cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)

4) Choose a sample application and follow the steps in the included README


Concepts
--------
CloudARK has two primary concepts - *environment* and *application*.

environment
  An environment consists of any cloud resource that is required by your application.
  This includes cloud databases, load balancers, container orchestration engines, etc.
  Environment is represented using a simple yaml format.

    Currently supported resources: AWS RDS, AWS DynamoDB, AWS ECS

application
  An application is a Docker container built from application source code.
  CloudARK assumes existence of Dockerfile in the application folder.
  An application is deployed on an environment.

CloudARK seamlessly binds the application to the environment as part of orchestrating its deployment.


Deployment to Amazon ECS
-------------------------

CloudARK assumes that you have done AWS setup and uses it (for example, using ~/.aws directory for
credentials). The ~/.aws directory will typically be created when you setup AWS CLI. If you don't have this directory
then follow these steps_.

.. _steps: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

Your AWS user will need to have following permissions in order to use CloudARK to deploy
containerized applications on AWS.

- AmazonRDSFullAccess
- AmazonEC2FullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonEC2ContainerServiceRole
- AmazonEC2ContainerServiceFullAccess
- AmazonEC2ContainerServiceAutoscaleRole
- AmazonEC2ContainerServiceforEC2Role



Available commands
-------------------

$ cld --help

usage: cld [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

CloudARK command-line tool - Make your containerized applications cloud ready.

Commands:

  environment create

  environment list

  environment show

  environment delete

  app deploy

  app redeploy

  app list

  app show

  app delete

  resource list

  resource show

