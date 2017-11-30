=================
CloudARK
=================

CloudARK is built to deploy full-stack microservices on Google GKE and Amazon ECS container platforms. Using CloudARK:

- Build and deploy microservices that use managed cloud services like Amazon RDS, Google Cloud SQL.

- Get ultimate dev/prod parity_ between local Docker environment and production cloud environment.

- Easily share application deployment plans with team members.

- Gain insights into your application and its cloud environment.

.. _parity: https://github.com/cloud-ark/cloudark-samples/blob/master/greetings/README.txt


CloudARK is based on *Platform-as-Code (PaC)* paradigm.
PaC enables defining and creating microservices using declarative definition
of platform elements consisting of:

- Application containers

- Container Orchestration Engine (COE) cluster

- Managed cloud services (e.g. Amazon RDS, Google Cloud SQL)


.. image:: ./docs/screenshots/Block-diagram-short.png
   :scale: 100%
   :align: center

Read this_ for more details about CloudARK

.. _this: https://cloud-ark.github.io/cloudark/docs/html/html/index.html


Try CloudARK
-------------

Tested on:

- Ubuntu 14.04, 16.04

- Mac OS (El Capitan 10.11.4)

Requires:

- Docker 1.6 and above

- Python 2.7

CloudARK requires Docker to be installed. If you do not have Docker, you can install it following steps from:

https://docs.docker.com/engine/installation/

On Mac OS, make sure the command shell from which you are installing CloudARK is able to run docker commands
without sudo. You can achieve this by executing following command once Docker VM is running in the shell:

eval "$(docker-machine env default)"


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

  app delete

  setup aws

  setup gcloud



Deploying on Google GKE
------------------------

  $ cld setup gcloud
    - This will request OAuth authorizations for gcloud sdk and gcloud auth library.
      Follow the prompts and provide the required input.

  $ ./restart-cloudark.sh


Deploying on Amazon ECS
------------------------

  $ cld setup aws
    - This will prompt you to enter AWS access_key_id, secret_access_key, region, output format.
      Follow the prompts and provide the required input.

  $ ./restart-cloudark.sh


Your AWS user will need to have following managed policies in order to do deployments using CloudARK.

- AmazonEC2FullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonEC2ContainerServiceFullAccess
- AmazonEC2ContainerServiceAutoscaleRole
- AmazonEC2ContainerServiceforEC2Role
- AmazonRDSFullAccess (if your application depends on RDS)

Additionally your AWS user will need to have the EC2 Container Service Role. Use these steps to create it:

-> AWS Web Console -> IAM -> Roles -> Create Role -> Select EC2 Container Service -> In "Select your use case" choose EC2 Container Service 
-> Next: Permissions -> Next: Review -> For role name give "EcsServiceRole" -> Hit "Create Role".

Finally you will also need to add IAM policy shown below which will grant permissions to the
ECS agent running on your ECS cluster instances to perform IAM actions
such as creating a ECS instance profile role and assuming that role.
This is required for the ECS agent to communicate with the ECS service.
Use these steps to create this policy:

-> AWS Web Console -> IAM -> Select your user in IAM -> Add permissions -> Attach existing policies directly -> Create Policy
-> Create Your Own Policy

In the Policy Document enter following policy. Replace <account-id> with your account id.

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



Screenshots
------------

1) Environment resource definition

   .. image:: ./docs/screenshots/wordpress/env-yaml.png

2) Create environment
   
   $ cld env create wpenv environment-rds-ecs.yaml
 
   .. image:: ./docs/screenshots/wordpress/env-create.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/env-show-available.png
      :scale: 125%

3) Create application container

   $ cld container create wordpresscontainer ecr
 
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

   $ cld app show 27

   .. image:: ./docs/screenshots/wordpress/app-deployment-complete.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/app-logs.png
      :scale: 125%


5) Deployed application (wordpress)

   .. image:: ./docs/screenshots/wordpress/wordpress-installed.png
      :scale: 125%

   .. image:: ./docs/screenshots/wordpress/wordpress-blog-page-with-elb.png
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
