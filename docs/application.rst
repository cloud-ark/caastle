Application
------------

An application is composed of a single or multiple Docker containers in CloudARK.

CloudARK offers ‘cld container create’ command to build your application container/s from your Docker files and push them to your registry of choice.
The container is appropriately tagged for AWS ECR or Google GCR to make it ready to run on COE target of your choice.

Application definition is done using our yaml format for single container applications or respective COE yaml format such as Kubernetes yaml format for multi-container applications. Note that for Kubernetes yaml format, currently only Pod definitions are supported. Support for ECS task yaml is planned.

Application definition includes URIs of the built containers from container registry, container inter-dependencies and any other run-time parameters to run each container.
Here is a sample app yaml definition for a single container wordpress application.

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

Application is deployed in an *environment*. The application deployment action takes
the name of the environment as input ('cld app deploy <app-name> <env-name> <app yaml>').
app.yaml contains definition of the application container image, the container port
and any environment variables.
As part of the deployment steps CloudARK binds the application container(s) to cloud resources
defined in the environment.

For single container applications currently a single instance of the application container is deployed on the cluster in the environment.

We have an issue open to support `scaling of application containers`__.

.. _scaling: https://github.com/cloud-ark/cloudark/issues/5

__ scaling_


Application type support matrix
--------------------------------

Following table shows currently supported application types, application definition formats, and the target COEs. 

+---------------------------------+-------------------------------+--------------+------------------------------+
| Type                            | Application definition format |   COE        |            Example           |
+=================================+===============================+==============+==============================+
| Single container                | app yaml (CloudARK format)    | ECS & GKE    |         hello-world_         |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Single cont + managed service   | app yaml (CloudARK format)    | ECS & GKE    |         wordpress_           |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Single cont + managed service   | pod yaml (Kubernetes format)  |    GKE       |         greetings_           |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Multi-container                 | pod yaml (Kubernetes format)  |    GKE       |   wordpress_kubernetes_pods_ |
+---------------------------------+-------------------------------+--------------+------------------------------+

Upcoming: Multi-container application on AWS (based on ECS Fargate or EKS)


.. _hello-world: https://github.com/cloud-ark/cloudark-samples/tree/master/hello-world

.. _greetings: https://github.com/cloud-ark/cloudark-samples/tree/master/greetings

.. _wordpress: https://github.com/cloud-ark/cloudark-samples/tree/master/wordpress/php5.6/apache

.. _wordpress_kubernetes_pods: https://github.com/cloud-ark/cloudark-samples/tree/master/wordpress-kubernetes-pods