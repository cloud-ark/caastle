Environment
------------

An environment is defined in a yaml file using declarative syntax.
Environment definition consists of two sections *cloud resources* and *app_deployment target*.
Here is an example of environment definition
containing AWS RDS as cloud resource and AWS ECS as application deployment target.

.. code-block:: yaml

   environment:
     resources:
       aws:
         - resource:
             type: rds
             configuration:
               engine: mysql
               flavor: db.m1.medium
     app_deployment:
       target: aws
       type: ecs

The *resources* section consists of one or more resource definitions.
A resource definition consists of the *type* attribute and an optional *configuration* directive.
The *type* attribute identifies the type of the resource to provision.
The *configuration* directive specifies how the resource should be configured.
This directive is made up of key-value pairs where the keys are the attributes
that are configurable on that resource. 

The *app_deployment* section consists of the *target* attribute and the *type* attribute.
The target attribute identifies the cloud on which the container orchestration engine (COE)
cluster should be created. The type attribute identifies the type of the COE.
Using target and type attributes we are able to capture different combinations of
clouds and COEs such as, <aws, ecs>, <aws, kubernetes>, <gcloud, gke>, etc.

CaaStle environment definition format is built to serve multi-cloud / cross-cloud scenarios so that developers can choose
managed cloud services and COE cluster from any hosting provider of their choice. The framework is extensible to accommodate even third-party managed cloud services.

An environment is created using 'cld environment create <env-name> <env yaml>' command.

Here are the currently supported resources in an environment definition in CaaStle.


**AWS resource types**

1) rds:

   *Configuration attributes: engine, flavor, policy*

   Default value for engine attribute is 'mysql'. Default value for flavor attribute is 'db.t1.micro'

   Possible values for flavor attribute are the corresponding values for RDS_

.. _RDS: https://aws.amazon.com/rds/instance-types/

   Support for additional rds engines_ is planned.

.. _engines: https://github.com/cloud-ark/cloudark/issues/122

   The policy attribute is used to control accessibility of the DB instance. This attribute contains
   a sub-attribute *access* whose value controls this aspect. If *access* is set to *open*, the RDS instance
   will be accessible from anywhere. If it is set to particular CIDR address then the instance will be
   accessible only from IP address in that CIDR subnet. An example of environment definition with these options can be seen here_.

.. _here: https://github.com/cloud-ark/cloudark-samples/blob/master/greetings/environment-rds-local.yaml

   The policy attribute is useful during development when you may want to connect to the RDS instance from your development machine.

2) ecs:

   *Configuration attributes: cluster_size, instance_type*

   Default value for cluster_size is 1. Default value for instance_type is t2.micro

   The configuration attributes for ecs are specified in the *app_deployment* section of the environment definition.

   Here are examples of environment definitions showing use of cluster_size_ and instance_type_ attributes.

.. _cluster_size: https://github.com/cloud-ark/cloudark-samples/blob/master/hello-world/environment-ecs-size-2.yaml

.. _instance_type: https://github.com/cloud-ark/cloudark-samples/blob/master/hello-world/environment-ecs-instance-type.yaml

   For the machine image, CaaStle uses AWS machine image that has ECS agent baked in.


**Google Cloud resource types**

1) cloudsql:

   *Configuration attributes: dbname, policy*

   The policy attribute is used to control accessibility of the DB instance. This attribute contains
   a sub-attribute *access* whose value controls this aspect. If *access* is set to *open*, the RDS instance
   will be accessible from anywhere. If it is set to particular CIDR address then the instance will be
   accessible only from IP address in that CIDR subnet. Note that this option is similar for cloudsql and rds as shown here_. 

   The db instance is created with db-n1-standard-1 tier type. We have an issue open_ to make this attribute settable.

.. _open: https://github.com/cloud-ark/cloudark/issues/123


2) gke:

   *Configuration attributes: cluster_size, instance_type*

   Default value for cluster_size is 1. Default value for instance_type is n1-standard-1

   The configuration attributes for gke are specified in the *app_deployment* section of the environment definition.
