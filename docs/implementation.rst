Implementation Details
-----------------------

Here are details of some of the implementation aspects of CloudARK.

**Communication between Platform elements**

CloudARK restricts the communication between various platform elements of an environment as follows.

For AWS, all the resources are created in `Default VPC currently`__. If an environment contains definition of RDS resource and ECS cluster resource, a security group
is added for the RDS instance that allows traffic only from the CIDR address of the ECS cluster in that environment.

.. _defvpc: https://github.com/cloud-ark/cloudark/issues/4 

__ defvpc_

For single container applications on Google cloud, the container is deployed in the `default namespace`__.

.. _gkedefaultns: https://github.com/cloud-ark/cloudark/issues/157

__ gkedefaultns_

For each such deployment a new global VPC network is created. Initially we were using default VPC network for this. However, there arose a situation with one of our users where their account did not have default VPC network. So we are now creating custom VPC network for each application deployment.

If an environment contains Cloud SQL as a platform element along with GKE cluster, the authorizedNetwork attribute of Cloud SQL is set to the IP address of the cluster node. This way only traffic arising from the cluster is able to connect and access the Google Cloud SQL instance. We are also planning to support the pattern of using `a sidecar proxy container`__ to establish connection between application container and Cloud SQL instance.

.. _sidecarproxy: https://github.com/cloud-ark/cloudark/issues/158

__ sidecarproxy_


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
   delete them from the AWS web console.


2) Google Cloud resources:
 
   CloudARK creates following Google cloud resources as part of environment creation
   and application deployment:
   - GKE cluster, Cloud SQL instance, GCR repository, VPC network, Kubernetes deployment, pods, services

   The resources are named using following pattern: <env-name>-<timestamp> or <app-name>-<timestamp>.

   All the resources are deleted when corresponding application or the environment is deleted.
   However, it will be a good idea to periodically verify this. If you find any stray
   resources corresponding to deleted applications or environments, manually
   delete them from the Google cloud web console.

   Note that custom VPC network for an application is *not getting deleted* currently.
   We have an open issue for this_

.. _this: https://github.com/cloud-ark/cloudark/issues/101

   So when you delete the application, delete the VPC network from the Google cloud console

   Similary when you delete a container, the GCR repository for it is not getting deleted_.

.. _deleted: https://github.com/cloud-ark/cloudark/issues/102

   Manually delete the repository after you have deleted the container.


3) Local Docker resources:

   Occassionally, CloudARK uses Docker as the mechanism for invoking native cloud CLI commands.
   Docker containers and Docker images created for this purpose are deleted by CloudARK.
   However, once in a while it will be a good idea to verify this and do cleanup actions given below,
   if required:

   $ docker ps -a | grep Exited | awk '{print $1}'  | xargs docker stop

   $ docker ps -a | grep Exited | awk '{print $1}'  | xargs docker rm

   $ docker images | grep none | awk '{print $3}' | xargs docker rmi

   Repeate the docker rmi command as many times as required by changing the grepped value
 