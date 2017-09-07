=================
CloudARK
=================

Environment-as-Code for Cloud Native Containerized Applications.

An environment for a cloud native containerized application consists of

a) COE (Container Orchestration Engine) cluster

b) Managed cloud services (e.g. Amazon RDS, Google Cloud SQL) and

Application containers are deployed on such an environment.

Currently such environments are not easy to create, share, and reproduce because managed cloud services are not integral part of the application architecture definition.

CloudARK offers ‘Environment-as-Code’ solution to declare and create cloud environments for containerized applications.
CloudARK allows developers to add managed cloud services as integral part of their micro services architecture definition.

Platform-as-a-service (PaaS) systems support managed service integration with applications, however,
these systems are increasingly being challenged by Docker and Container-as-a-Service (CaaS) systems
as most of the traditional PaaS functionality is now available through them. One area where they
lack currently is managed services integration. So the alternative approach
that is used today is to develop custom solution that combines CaaS + Infrastructure as code + custom scripting
for binding of managed services with containerized applications.

Environment-as-Code approach exemplified by CloudARK simplifies this alternative approach
with a *non-hosted command-line* tool that supports declarative specification of an application's cloud environment
and commands to create and reproduce such environments. This leads to following benefits:

a) Environment definition can be reused for different applications

b) Environment definition can be shared between team members

c) CloudARK commands can be integrated in your custom workflows and scripts either locally or in a CI workflow


Try CloudARK
-------------

CloudARK has been developed and tested on Ubuntu 14.04 and Mac OS (Darwin)

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


Read this_ for more details about CloudARK

.. _this: https://cloud-ark.github.io/cloudark/docs/html/html/index.html



Concepts
--------
CloudARK has two primary concepts - *environment* and *application*.

environment
  An environment consists of any cloud resource that is required by your application.
  This includes cloud databases, load balancers, container orchestration engine cluster, etc.
  Environment is represented using a simple yaml format.

    Currently supported: AWS RDS, AWS ECS, AWS DynamoDB

    Coming soon: Google Cloud SQL, Kubernetes (GKE)

application
  An application is a Docker container built from application source code.
  CloudARK assumes existence of Dockerfile in the application folder.
  An application is deployed on an environment and is bound to the resources
  provisioned as part of that environment.

CloudARK seamlessly binds the application to the environment as part of orchestrating its deployment.


Deployment to Amazon ECS
-------------------------

CloudARK assumes that you have done AWS setup and uses it during deployment. For example, CloudARK uses ~/.aws directory 
to read aws 
credentials. The ~/.aws directory will typically be created when you setup AWS CLI. If you don't have this directory
then follow these steps_ to do AWS setup.

.. _steps: http://docs.aws.amazon.com/cli/latest/userguide/installing.html

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

::
  $ cld --help

  usage: cld [--version] [-v | -q] [--log-file LOG_FILE] [-h] [--debug]

  CloudARK command-line tool to create and manage cloud environments for
  containerized applications.

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


Screenshots
------------

1) Environment resource definition

   .. image:: ./docs/screenshots/env-yaml.png

2) Create environment
   
   $ cld environment create staging environment-rds-ecs.yaml
 
   .. image:: ./docs/screenshots/env-create-show.png
      :scale: 125%

3) Deploy application

   $ cld app deploy greetings --env-id 27

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

Devdatta Kulkarni: devdattakulkarni at gmail 


