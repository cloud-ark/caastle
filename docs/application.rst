Application
------------

An application can be composed of a single or multiple Docker containers in CloudARK.

CloudARK offers ‘cld container *’ commands to build your application containers from your Docker files and push them to your registry of choice.
The container is appropriate tagged for AWS ECR or Google GCR to make it ready to run on COE target of your choice.

Application definition is done using our yaml format (for single container applications) or respective COE (Kubernetes / ECS) yaml format (for multi-container applications). Application definition generally includes URIs to the built containers from container registry, container interdependencies and any other run-time parameters to run each container.  
Here is a sample app.yaml based application definition for a single container wordpress application.


Application is deployed on an *environment*. The application deployment action takes
the name of the environment as input (*cld app deploy {app-name} {env-name} {app.yaml}*).
app.yaml contains definition of the application container image, the container port
and any environment variables.

CloudARK provides commands to build the application container and push it to public container
registry such as Amazon ECR or Google GCR.

As part of the deployment step CloudARK binds the application container(s) to cloud resources
in the environment defined in application definition file. 
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


*Defining Environment Variables*

The environment variables are set using following format: *CLOUDARK_<TYPE>_<Attribute>*.
The *TYPE* is one of the supported resource types (represented in uppercase).
*Attribute* is the exact name of one of the output attributes of the provisioned resource.
Output attributes available for a resource can be obtained by querying the resource
using *cld resource show {env_name}* command.
