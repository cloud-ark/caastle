Environment
------------

An environment is defined in a yaml file using declarative syntax.
Environment definition consists of two sections *resources* and *app_deployment*.
Here is an example of environment definition
containing AWS RDS resource and AWS ECS for application deployment.

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
Currently supported types are 'rds', 'dynamodb'. 
The *configuration* directive specifies how the resource should be configured.
This directive is made up of key-value pairs where the keys are the attributes
that are configurable on that resource.

The *app_deployment* section consists of the *target* attribute and the *type* attribute.
The target attribute identifies the cloud on which the container orchestration engine (COE)
cluster should be created. The type attribute identifies the type of the COE.
Using target and type attributes we are able to capture different combinations of
clouds and COEs such as, <aws, ecs>, <aws, kubernetes>, <gcloud, gke>, <openstack, magnum>, etc.
Currently supported options are: <aws, ecs> and <gcloud, gke>

The reason behind separating resources and application deployment in the environment
definition is to support cross-cloud deployments in the future where one can deploy application
on one cloud and bind it to managed resources from another cloud. 

An environment is created using *cld environment create {env}* command.






