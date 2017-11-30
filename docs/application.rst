Application
------------

An application is a Docker container in CloudARK. CloudARK assumes that Dockerfile
is present in the application directory.

Application is deployed on an *environment*. The application deployment action takes
the name of the environment as input (*cld app deploy {app-name} {env-name} {app.yaml}*).
app.yaml contains definition of the application container image, the container port
and any environment variables.

CloudARK provides commands to build the application container and push it to public container
registry such as Amazon ECR or Google GCR.

As part of the deployment step CloudARK binds the application container to resources
in the environment through environment variables
defined in app.yaml file. For example here is a Dockerfile from greetings_ application.

.. _greetings: https://github.com/cloud-ark/cloudark-samples/tree/master/greetings

.. code-block:: Dockerfile

   FROM ubuntu:14.04
   RUN apt-get update -y \ 
       && apt-get install -y python-setuptools python-pip
   ADD requirements.txt /src/requirements.txt
   RUN cd /src; pip install -r requirements.txt
   ADD . /src
   EXPOSE 5000
   CMD ["python", "/src/application.py"]

.. code-block:: app.yaml
   app:
     image: <image_uri>
     container_port: 5000
     env:
       PASSWORD: $CLOUDARK_RDS_MasterUserPassword
       DB: $CLOUDARK_RDS_DBName
       HOST: $CLOUDARK_RDS_Address
       USER: $CLOUDARK_RDS_MasterUsername


The environment variables are set using following format: *CLOUDARK_<TYPE>_<Attribute>*.
The *TYPE* is one of the supported resource types (represented in uppercase).
*Attribute* is the exact name of one of the output attributes of the provisioned resource.
Output attributes available for a resource can be obtained by querying the resource
using *cld resource show {env_name}* command.
