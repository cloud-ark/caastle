Application
------------

An application is defined as Docker container. CloudARK assumes that Dockerfile
is present in the application directory from which CloudARK commands would be run.

Application is deployed on an *environment*. The application deployment action takes
the id of the environment as input. CloudARK builds the docker container image for
the application and then deploys it on the COE cluster created as part of the specified
environmnet.

Application is bound to resources in the environment through environment variables
defined in the Dockerfile. For example here is a Dockerfile from greetings_ application.

.. _greetings: https://github.com/cloud-ark/cloudark-samples/tree/master/greetings

.. code-block:: Dockerfile

   FROM ubuntu:14.04
   RUN apt-get update -y \ 
       && apt-get install -y python-setuptools python-pip
   ADD requirements.txt /src/requirements.txt
   RUN cd /src; pip install -r requirements.txt
   ADD . /src
   EXPOSE 5000
   ENV  PASSWORD $CLOUDARK_RDS_MasterUserPassword
   ENV  DB $CLOUDARK_RDS_DBName
   ENV  HOST $CLOUDARK_RDS_Address
   ENV  USER $CLOUDARK_RDS_MasterUsername
   CMD ["python", "/src/application.py"]

The environment variables are set using following format: *CLOUDARK_<TYPE>_<Attribute>*.
The *TYPE* is one of the supported resource types (represented in uppercase).
*Attribute* is the exact name of one of the output attributes of the provisioned resource.
Output attributes available for a resource can be obtained by querying the resource
using *cld resource list* command.
