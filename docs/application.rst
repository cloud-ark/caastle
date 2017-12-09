Application
------------

An application can be composed of a single or multiple Docker containers in CloudARK.

CloudARK offers ‘cld container ’ set of commands to build your application containers from your Docker files and push them to your registry of choice.
The container is appropriately tagged for AWS ECR or Google GCR to make it ready to run on COE target of your choice.

Application definition is done using our yaml format for single container applications or respective COE (Kubernetes / ECS) yaml format for multi-container applications. 
Application definition includes URIs of the built containers from container registry, container interdependencies and any other run-time parameters to run each container.
Here is a sample app.yaml based application definition for a single container wordpress application.

.. _greetings: https://github.com/cloud-ark/cloudark-samples/tree/master/greetings

.. code-block:: yaml

   app:
     image: <image_uri>
     container_port: 5000
     env:
       PASSWORD: $CLOUDARK_RDS_MasterUserPassword
       DB: $CLOUDARK_RDS_DBName
       HOST: $CLOUDARK_RDS_Address
       USER: $CLOUDARK_RDS_MasterUsername

Our yaml format for single container applications supports following attributes: *image*, *container_port*, *host_port*, *env*.
Default value for host_port is 80.

Application is deployed on an *environment*. The application deployment action takes
the name of the environment as input ('cld app deploy <app-name> <env-name> <app yaml>').
app.yaml contains definition of the application container image, the container port
and any environment variables.

As part of the deployment step CloudARK binds the application container(s) to cloud resources
defined in the environment.

For single container applications currently a single instance of the application container is deployed on the cluster in the environment.

We have an issue open to support `scaling of application containers`__.

.. _scaling: https://github.com/cloud-ark/cloudark/issues/5

__ scaling_
