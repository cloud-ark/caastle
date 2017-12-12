Notes
------

1) AWS Cloud resources:

   CloudARK creates following AWS resources as part of environment creation
   and application deployment:
   - security group, load balancer, ssh keypairs, ECS cluster, task definitions,
     ECR repository

   All these resources are deleted when the application and the environment are deleted.
   However, it will be a good idea to periodically verify this. If you find any stray
   resources corresponding to deleted applications and environments, manually
   delete them from the AWS console.


2) Google Cloud resources:
 
   CloudARK creates following Google cloud resources as part of environment creation
   and application deployment:
   - VPC network, GCR repository, GKE cluster

   The VPC network is *not getting deleted* currently. We have an open issue for this_

.. _this: https://github.com/cloud-ark/cloudark/issues/101

   So when you delete the application, delete the VPC network from the Google cloud console

   Similary when you delete a container, the GCR repository for it is not getting deleted_.

.. _deleted: https://github.com/cloud-ark/cloudark/issues/102

   Manually delete the repository after you have deleted the container.


3) Local Docker resources:

   CloudARK uses Docker as the mechanism for invoking native cloud CLI commands occassionally.
   The Docker containers created for this purpose are deleted by CloudARK. Once in a while it
   will be a good idea to verify this and do cleanup actions given below:

   $ docker ps -a | grep Exited | awk '{print $1}'  | xargs docker stop
   $ docker ps -a | grep Exited | awk '{print $1}'  | xargs docker rm
   $ docker images | grep none | awk '{print $3}' | xargs docker rmi

   Repeate the docker rmi command as many times as required by changing the grepped value
   
