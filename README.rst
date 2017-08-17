=================
CloudARK
=================
CloudARK makes your containerized applications *cloud ready*.

Today, deploying containerized applications on public clouds involves following steps:

1) Provision cloud services (such as Amazon RDS)
2) Provision container orchestration engine (COE) cluster (such as Amazon ECS or GKE)
3) Build application containers
4) Bind containers to cloud services
5) Deploy containers on COE cluster

Different tools are required for each of these steps currently.

CloudARK is a command-line tool that unifies all these steps providing a unified experience for 
deploying your containerized applications on public clouds.


Try cloudark
-------------
1) Clone this repository

2) Run cloudark:

   - ./install.sh

3) Clone the cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)

4) Choose a sample application and follow the steps in the included README


Concepts
--------
Cloudark has two primary concepts - *environment* and *application*.

environment
  An environment consists of any cloud resource that is required by the application.
  This includes cloud databases, load balancers, container orchestration engines, etc.
  Environment is represented using a simple yaml format.

application
  An application is something for which a Docker container can be built.
  Application is deployed on an environment. For application representation, 
 we use Dockerfile and assume its existence in your application directory.

Cloudark seamlessly binds the application to the environment as part of orchestrating
its deployment on the environment.


Deployment to Amazon (ECS)
---------------------------
1) Sign up for Amazon AWS account
2) Login to Amazon AWS web console and from the IAM panel do following:

   - Create a IAM User (choose any name)

   - Grant following permission to the user by clicking the "Add permissions" button on the user panel.

     - AmazonRDSFullAccess
     - AmazonEC2FullAccess
     - AmazonEC2ContainerRegistryFullAccess
     - AmazonEC2ContainerServiceRole
     - AmazonEC2ContainerServiceFullAccess
     - AmazonEC2ContainerServiceAutoscaleRole
     - AmazonEC2ContainerServiceforEC2Role

3) Note down SECRET_ACCESS_KEY and ACCESS_KEY_ID for this user. Provide these values when asked by cld.

4) Deploy hello-world sample application:

   - Navigate to the application folder (cd $APPROPRIATE-PATH/cloudark-samples/hello-world)

   - Deploy application:

     $ cld app deploy --target aws
     
     +------------------+-----------+------------+
     |     App Name     | Deploy ID |    Cloud   |
     +------------------+-----------+------------+
     | hello-world      |    1      |     aws    |
     +------------------+-----------+------------+

5) Check deployment status

   $ cld app show --deploy-id 2

   +------------------+-----------+---------------------+--------------+---------------------------------------+
   |     App Name     | Deploy ID |        Status       |     Cloud    |                App URL                |
   +------------------+-----------+---------------------+--------------+---------------------------------------+
   | hello-world      |    1      | DEPLOYMENT_COMPLETE |      aws     | <App URL on AWS>                      |
   +------------------+-----------+---------------------+--------------+---------------------------------------+
