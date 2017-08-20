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

Note: CloudARK requires Docker to be installed. If you don't have Docker, you can install it_.

.. _it: https://docs.docker.com/engine/installation/



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

