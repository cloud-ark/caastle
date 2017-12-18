Implementation Details
-----------------------

Here are details of some of the implementation aspects of CloudARK.

**Communication between Platform elements**

CloudARK restricts the communication between various platform elements of an environment as follows.

For AWS, all the resources are created in `Default VPC currently`__. If an environment contains definition of RDS resource and ECS cluster resource, a security group
is added for the RDS instance that allows traffic only from the CIDR address of the ECS cluster in that environment. CloudARK currently uses the default Docker bridge networking mode for ECS tasks that are created for an application. We will revisit this choice when we add support for Fargate launch type for ECS deployments.

.. _defvpc: https://github.com/cloud-ark/cloudark/issues/4 

__ defvpc_


For single container applications on Google cloud, the container is deployed in the `default namespace`__.

.. _gkedefaultns: https://github.com/cloud-ark/cloudark/issues/157

__ gkedefaultns_

For each such deployment a new global VPC network is created. Initially we were using default VPC network for this. However, we experienced that one of our beta users `did not have default VPC network`__. So we are now creating custom VPC network for each application deployment.

.. _network: https://github.com/cloud-ark/cloudark/issues/162

__ network_

If an environment contains Cloud SQL as a platform element along with GKE cluster, the authorizedNetwork attribute of Cloud SQL is set to the IP address of the cluster node. This way only traffic arising from the cluster is able to connect and access the Google Cloud SQL instance. We are also planning to support the pattern of using `a sidecar proxy container`__ to establish connection between application container and Cloud SQL instance.

.. _sidecarproxy: https://github.com/cloud-ark/cloudark/issues/158

__ sidecarproxy_

If a cloud provider has implemented a `Service Broker`__, CloudARK's extensible architecture can accommodate it for provisioning of required resources.

.. _servicebroker: https://www.openservicebrokerapi.org

__ servicebroker_


**Cloud Resources**

CloudARK creates following resources as part of environment creation and application deployments.

1) AWS resources:

   CloudARK creates following AWS resources as part of environment creation
   and application deployment:
   - ECS cluster, ssh key pairs, ECR repository, RDS instances, security groups, load balancer, ECS task definitions, ECS services

   All the resources are named using following pattern: <env-name>-<timestamp> or <app-name>-<timestamp>.

   All the resources are deleted when corresponding application or the environment is deleted.
   However, it will be a good idea to periodically verify this. If you find any stray
   resources corresponding to deleted applications or environments, manually
   delete them from the AWS web console. We encourage users to open a ticket so that we can fix such
   bugs in CloudARK.


2) Google Cloud resources:
 
   CloudARK creates following Google cloud resources as part of environment creation
   and application deployment:
   - GKE cluster, Cloud SQL instance, GCR repository, VPC network, Kubernetes deployment, pods, services

   The resources are named using following pattern: <env-name>-<timestamp> or <app-name>-<timestamp>.

   All the resources are deleted when corresponding application or the environment is deleted.
   However, it will be a good idea to periodically verify this. If you find any stray
   resources corresponding to deleted applications or environments, manually
   delete them from the Google cloud web console. We encourage users to open a ticket so that we
   can fix such bugs in CloudARK.

   Note that custom VPC network for an application is *not getting deleted* currently.
   We have an open issue for this_

.. _this: https://github.com/cloud-ark/cloudark/issues/101

   So when you delete the application, delete the VPC network from the Google cloud console

   Similarly when you delete a container, the GCR repository for it is not getting deleted_.

.. _deleted: https://github.com/cloud-ark/cloudark/issues/102

   Manually delete the repository after you have deleted the container.


3) Local Docker resources:

   Occasionally, CloudARK uses Docker as the mechanism for invoking native cloud CLI commands.
   Docker containers and Docker images created for this purpose are deleted by CloudARK.
   However, once in a while it will be a good idea to verify this and do cleanup actions given below,
   if required:

.. code:: bash

    $ docker ps -a | grep Exited | awk '{print $1}'  | xargs docker stop

    $ docker ps -a | grep Exited | awk '{print $1}'  | xargs docker rm

    $ docker images | grep none | awk '{print $3}' | xargs docker rmi

   Repeat the docker rmi command as many times as required by changing the grepped value
 
**CloudARK's internal state**

CloudARK stores its internal state in the home folder inside .cld directory.
The database state is stored in ~/.cld/data/deployments/cld.sqlite.
Environment, Container, and Application related files that are generated by CloudARK for deployment purpose are stored in separate directories inside ~/.cld/data/deployments. You can view all the artifacts that CloudARK generates for each platform element inside the corresponding directory.

Moreover, CloudARK aims to be a *soft state* system. There is no restriction if you want to 
directly modify any platform element provisioned by CloudARK through the corresponding Cloud's web console.
In the future releases of CloudARK, the internal state will be synced with the state of platform elements on the Cloud.


**Application logs**

CloudARK provides 'cld app logs <app-name>' command to retrieve application's deployment and runtime logs.

The deployment logs are the logs generated by the target COE when it deploys the application container. Runtime logs on the other hand are the logs generated by the application itself. On GKE, deployment logs are obtained using 'kubectl describe pods <pod-name>' command and runtime logs are obtained using 'kubectl logs <pod-name>' command. On AWS, deployment logs correspond to the logs generated by the ecs agent running on a cluster instance. The runtime logs correspond to the logs generated by the application docker container running on a cluster instance. Both these logs are fetched from the cluster instance remotely.
