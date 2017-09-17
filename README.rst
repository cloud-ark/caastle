=================
CloudARK
=================

CloudARK is a *command-line tool* that offers ability to declare and create cloud environments for containerized applications.
An environment for containerized cloud application consists of following components:

a) Container Orchestration Engine (COE) cluster

b) Managed cloud services (e.g. Amazon RDS, Google Cloud SQL)

c) Application containers

CloudARK creates all the environment components, seamlessly binding them together.
It is a non-hosted PaaS alternative for containerized cloud applications.

Based on our survey 38% cloud developers use managed cloud services with their containerized cloud applications today.
However, consuming these services within containerized applications is not straightforward.
These services are not integral part of application architecture definition and require separate provisioning and binding effort.
Platform-as-a-service (PaaS) systems support managed services integration with applications, however, PaaS's hosted architecture is increasingly seen as an
overhead given most of the traditional PaaS functionality is now available in Docker and Container-as-a-service (CaaS) systems.
The alternative approach today is to develop a custom solution using
CaaS + Infrastructure-as-Code systems (like TerraForm) to provision managed cloud services + additional scripting to bind managed services with containerized applications.
Environment-as-Code implementation by CloudARK simplifies this alternative approach by supporting a declarative model
for defining the environment and a set of commands to create and provision the environment components, which leads to following benefits:

a) No need to develop custom scripts for managed service provisioning and their binding to containerized applications

b) CloudARK commands can be integrated in your custom workflows and scripts, either locally or within CI setup

c) Environment definition can be shared between team members

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

   .. image:: ./docs/screenshots/env-yaml.png

2) Create environment
   
   $ cld env create staging environment-rds-ecs.yaml
 
   .. image:: ./docs/screenshots/env-create-show.png
      :scale: 125%

3) Deploy application

   $ cld app deploy greetings 27

   .. image:: ./docs/screenshots/app-deploy.png
      :scale: 125%

4) Check application status

   $ cld app show 17

   .. image:: ./docs/screenshots/app-deployment-complete.png
      :scale: 125%

5) Deployed application

   .. image:: ./docs/screenshots/deployed-app.png
      :scale: 125%

6) AWS console

   .. image:: ./docs/screenshots/rds-aws-console.png
      :scale: 125%

   .. image:: ./docs/screenshots/ecs-aws-console.png
      :scale: 125%

   .. image:: ./docs/screenshots/ecs-task-definition.png
      :scale: 125%

   .. image:: ./docs/screenshots/ecs-repository.png
      :scale: 125%



Contact:
--------

Devdatta Kulkarni: devdattakulkarni at gmail dot com


