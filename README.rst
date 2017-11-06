=================
CloudARK
=================

CloudARK enables full-stack deployment of microservices on Google GKE and Amazon ECS container platforms. Using CloudARK:

- Build and deploy microservices that use managed cloud services like Amazon RDS, Google Cloud SQL.

- Get ultimate dev/prod parity_ between local Docker environment and production cloud environment.

- Easily share application deployment plans with team members.

- Gain insights into your application and its cloud environment.

.. _parity: https://github.com/cloud-ark/cloudark-samples/blob/master/greetings/README.txt


CloudARK is based on the concept of *Platform-as-Code (PaC)*.
PaC enables defining and creating micro services using a declarative definition of
of its platform elements, consisting of:

- Container Orchestration Engine (COE) cluster

- Managed cloud services (e.g. Amazon RDS, Google Cloud SQL)

- Application containers

.. image:: ./docs/screenshots/Block-diagram-short.png
   :scale: 100%
   :align: center

Read this_ for more details about CloudARK

.. _this: https://cloud-ark.github.io/cloudark/docs/html/html/index.html


Try CloudARK
-------------

Supported Platforms and Languages:

- Ubuntu 14.04, 16.04

- Mac OS (El Capitan 10.11.4)

- Docker 1.6 and above

- Python 2.7

CloudARK requires Docker to be installed. If you don't have Docker, you can install it following steps from:

https://docs.docker.com/engine/installation/

Once you have installed Docker follow these steps:


1) Clone this repository

2) Install CloudARK
   $ ./install.sh

3) Do cloud setup

   $ cld setup aws

   $ cld setup gcloud

4) Start CloudARK server

   $ ./start-cloudark.sh

5) Clone the cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)

6) Choose a sample application and follow the steps in the included README



Deploying on Google GKE
------------------------

  $ cld setup gcloud
    - This will create a gcloud user token and application token which will be used by CloudARK for deployment.
      Follow the instructions to generate these tokens.

  $ ./restart-cloudark.sh


Deploying on Amazon ECS
------------------------

  $ cld setup aws
    - This will prompt you to enter AWS access_key_id, secret_access_key, region, output format.
      Follow the prompts and provide the required input.

  $ ./restart-cloudark.sh


Your AWS user will need to have following managed policies in order to use CloudARK to deploy
containerized applications on Amazon ECS.

- AmazonEC2FullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonEC2ContainerServiceFullAccess
- AmazonEC2ContainerServiceAutoscaleRole
- AmazonEC2ContainerServiceforEC2Role
- AmazonRDSFullAccess (if your application depends on RDS)

Your AWS user will need to have the EC2 Container Service Role. Use these steps to create it:

-> AWS Web Console -> IAM -> Roles -> Create Role -> Select EC2 Container Service -> In "Select your use case" choose EC2 Container Service 
-> Next: Permissions -> Next: Review -> For role name give "EcsServiceRole" -> Hit "Create Role".

You will also need to add IAM policy shown below which will grant permissions to the
ECS agent running on your ECS cluster instances to perform IAM actions
such as create a ECS instance profile role and assume that role.
These permissions are required for the ECS agent to communicate with the ECS service.

Use these steps to create it:

-> AWS Web Console -> IAM -> Select your user in IAM -> Add permissions -> Attach existing policies directly -> Create Policy
-> Create Your Own Policy

In the Policy Document enter the following policy. Replace <account-id> with your account id.

::

  {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": "iam:*",
              "Resource": ["arn:aws:iam::<account-id>:role/*",
                           "arn:aws:iam::<account-id>:instance-profile/*]"
          }
      ]
  }

Once the policy is created attach it to your user.


Available commands
-------------------


$ cld --help

usage: cld [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

CloudARK command-line tool to create and manage cloud environments for
containerized applications.

Commands:

  env create

  env list

  env show

  env delete

  app deploy

  app redeploy

  app list

  app show

  app delete

  resource list

  resource show

  setup aws

  setup gcloud


Screenshots
------------

1) Environment resource definition

   .. image:: ./docs/screenshots/wordpress/env-yaml.png

2) Create environment
   
   $ cld env create staging environment-rds-ecs.yaml
 
   .. image:: ./docs/screenshots/wordpress/env-create-1.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/env-create-2.png
      :scale: 125%

3) Deploy application

   $ cld app deploy wordpress 12 --memory 1000

   .. image:: ./docs/screenshots/wordpress/app-deploy-1.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/app-deploy-2.png
      :scale: 125%


4) Check application status

   $ cld app show 27

   .. image:: ./docs/screenshots/wordpress/app-deployment-complete.png
      :scale: 125%

5) Deployed application (wordpress)

   .. image:: ./docs/screenshots/wordpress/wordpress-deployed-1.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/wordpress-using-elb.png
      :scale: 125%

6) AWS console

   .. image:: ./docs/screenshots/wordpress/RDS.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/ECS-cluster.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/Task-Definition.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/ECR.png
      :scale: 125%



Contact:
--------

Devdatta Kulkarni: devdatta at cloudark dot io
