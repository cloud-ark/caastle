=================
CloudARK
=================

CloudARK is a *command-line tool* that offers ability to declare, create, and share environments of containerized cloud applications.
An environment of containerized cloud application consists of following components:

a) Container Orchestration Engine (COE) cluster

b) Managed cloud services (e.g. Amazon RDS, Google Cloud SQL)

c) Application containers

.. image:: ./docs/screenshots/Block-diagram-short.png
   :scale: 100%
   :align: center

CloudARK offers ability to easily define these environments, provision its components,
and seamlessly bind them together at runtime.

CloudARK is based on the concept of *Environment-as-Code*.
Our view is that it should be possible to treat the environment of containerized applications
similar to source code -- it should be version controlled, easy to modify for your needs, easy to integrate in your own workflows,
and sharable between team members.

Following are two key issues in creating cloud environments for containerized cloud applications today:

a) Managed cloud services are not integral part of application architecture definition and require separate provisioning and binding effort.

b) Differences in deploying an application to Docker and Container Orchestration Engines (COEs) add to the complexity of creating
   consistent deployment workflows during development.

Some of the existing Platform-as-a-service (PaaS) systems do support managed services integration with applications, however,
their hosted architecture is increasingly seen as an
overhead given most of the traditional PaaS functionality is now available in Docker and Container-as-a-service (CaaS) systems.
The alternative approach today is to develop a custom solution using
CaaS + Infrastructure-as-Code systems like TerraForm (to provision managed cloud services) + additional scripting (to bind managed services with containerized applications).
CloudARK simplifies this alternative approach by supporting a declarative model
for defining and creating environments of containerized applications, seamlessly binding
managed services with application containers at runtime. This leads to following benefits:

a) Extend application architecture definition to include cloud resources

b) Uniform workflow across Docker and COEs

c) Integrate easily with your custom DevOps workflows

*Currently Supported: Local Docker, AWS ECS, AWS RDS, AWS DynamoDB*

*Coming soon: GKE, Google Cloud SQL*

Read this_ for more details about CloudARK

.. _this: https://cloud-ark.github.io/cloudark/docs/html/html/index.html


Try CloudARK
-------------

CloudARK has been developed and tested on Ubuntu (14.04) and Mac OS (Darwin)

1) Clone this repository

2) Install CloudARK:

     ./install.sh

     - If above fails for some reason follow these steps:
       
       - Open a terminal and start the cloudark server process:
         (a) cd <cloudark directory>
         (b) virtualenv cloudark-env
         (c) source cloudark-env/bin/activate
         (d) pip install -r requirements.txt
         (e) python server/fmserver.py
  
       - Open another terminal and install cloudark client:
         (a) cd <cloudark directory>
	 (b) source cloudark-env/bin/activate
         (c) cd client
         (d) python setup.py install

3) Clone the cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)

4) Choose a sample application and follow the steps in the included README

Note: CloudARK requires Docker to be installed. If you don't have Docker, you can install it_.

.. _it: https://docs.docker.com/engine/installation/



Deployment to Amazon ECS
-------------------------

CloudARK assumes that you have done AWS setup and uses it during deployment. For example, CloudARK uses ~/.aws directory 
to read aws credentials.  If you don't have this directory then follow these_ steps to do AWS setup.

.. _these: http://docs.aws.amazon.com/cli/latest/userguide/installing.html

Your AWS user will need to have following managed policies in order to use CloudARK to deploy
containerized applications on AWS.

- AmazonEC2FullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonEC2ContainerServiceRole
- AmazonEC2ContainerServiceFullAccess
- AmazonEC2ContainerServiceAutoscaleRole
- AmazonEC2ContainerServiceforEC2Role

Include AmazonRDSFullAccess policy as well if your application depends on RDS.

You will also need to add IAM policy shown below which will grant permissions to the
ECS agent running on your ECS cluster instances to perform IAM actions
such as create a ECS instance profile role and assume that role.
These permissions are required for the ECS agent to communicate with the ECS service.

Select your user in IAM -> Add permissions -> Attach existing policies directly -> Create Policy
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


