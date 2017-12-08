Environment Variables
----------------------

The environment variables are defined in application yaml file under *env* section for
single container applications. For multi-container applications environment variables
would be defined in the standard approach in the respective yaml file of the target system (GKE or ECS).

An example of environment variable definition in application yaml is shown below:

.. code-block:: yaml

   app:
     env:
       PASSWORD: $CLOUDARK_RDS_MasterUserPassword
       DB: $CLOUDARK_RDS_DBName
       HOST: $CLOUDARK_RDS_Address
       USER: $CLOUDARK_RDS_MasterUsername

For binding application container with managed services defined in the environment
following format is defined: $CLOUDARK_<TYPE>_<Attribute>*.
The *TYPE* is one of the supported resource types (represented in uppercase).
*Attribute* is the exact name of one of the output attributes of the provisioned resource.
Output attributes available for a resource can be obtained by querying the resource
using *cld resource show {env_name}* command.

In the above example, by defining the value of the PASSWORD environment variable as
$CLOUDARK_RDS_MasterUserPassword, the value will be set to the MasterUserPassword of
the RDS instance provisioned in the environment in which the application is deployed.
For instance, if you have created two environments *test* and *staging* then when
you deploy the application in *test* environment (using cld app deploy myapp test app.yaml),
the value of PASSWORD will be set to the value of RDS instance in the test environment.
On the other hand, if you deploy it in *staging* environment (using cld app deploy myapp staging app.yaml),
the value will be set as per the value of RDS instance in the staging environment.