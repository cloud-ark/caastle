Environment Variables
----------------------

CaaStle application definition format: 

Environment variables are defined in application yaml file under *env* section for
single container applications. 

An example of environment variable definition in application yaml is shown below:

.. code-block:: yaml

   app:
     env:
       PASSWORD: $CLOUDARK_RDS_MasterUserPassword
       DB: $CLOUDARK_RDS_DBName
       HOST: $CLOUDARK_RDS_Address
       USER: $CLOUDARK_RDS_MasterUsername


Kubernetes format:

For multi-container applications environment variables
can be defined in the standard approach in the respective yaml file of the target system (GKE or ECS).

An example of environment variable definition for Kubernetes pods is shown below:

.. code-block:: yaml

   apiVersion: v1
   kind: Pod
   metadata:
     name: greetings1
     labels:
       name: greetings1
   spec:
     containers:
       - image: us.gcr.io/cloudark-test-gke/greetpod:1512924392448
         name: wordpress
         ports:
         - containerPort: 5000
         env:
           - name: "PASSWORD"
             value: $CLOUDARK_CLOUDSQL_Password
           - name: "DB"
             value: $CLOUDARK_CLOUDSQL_DBName
           - name: "HOST"
             value: $CLOUDARK_CLOUDSQL_Address
           - name: "USER"
             value: $CLOUDARK_CLOUDSQL_Username


Environment variables are defined as key:value pairs.

An application is bound to managed services in the environment through the environment variables
following `12-factor design principles`__.

.. _Twelve: https://12factor.net/config

__ Twelve_

The value of the parameter that needs to be bound to an attribute of the cloud resource in an environment
is set as an *interpolated variables*. CaaStle defines following format for this purpose: $CLOUDARK_<TYPE>_<Attribute>.
The *TYPE* is one of the supported resource types (represented in uppercase).
*Attribute* is the exact name of one of the output attributes of the provisioned resource.
All the output attributes available for a resource can be obtained by querying the resource
using 'cld resource show <env-name>' command.

In the above example, by defining the value of the PASSWORD environment variable as
a interpolated value of $CLOUDARK_RDS_MasterUserPassword,
CaaStle will set the value of the PASSWORD to the MasterUserPassword of
the RDS instance provisioned in the environment in which the application is deployed.

Mechanism of interpolated variables makes the application definition reusable across environments.
For instance, suppose you have created two environments *test* and *staging*. When
you deploy the application in *test* environment (using 'cld app deploy myapp test app.yaml'),
the value of PASSWORD will be set to the value of MasterUserPassword of the RDS instance in the test environment.
On the other hand, if you deploy the application in *staging* environment (using 'cld app deploy myapp staging app.yaml'),
the value will be set as per the value of MasterUserPassword of the RDS instance in the staging environment.
