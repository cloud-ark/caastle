Hello World
------------

This example shows deployment of web application written using Python.

The Dockerfile defines application build steps.

Several environment yaml files are available in the folder:
a) environment-local.yaml should be used for local deployment
b) environment-ecs.yaml should be used for AWS ECS deployment
c) environment-ecs-instance-type.yaml shows how to customize the
   instance type of the ECS cluster VMs (default instancy type is
   t2.micro)
d) environment-ecs-size-2.yaml shows how to customize the size
   of the ECS cluster (default cluster size is 1)
e) environment-gke.yaml - for deployments on Google Container Engine (GKE)


===============
Deploy Locally
===============

$ cld env create env-local environment-local.yaml

$ cld container create cont1 local

Edit app.yaml to include image id obtained from output of command:

$ cld container show cont1

$ cld app deploy hello-world-1 env-local app.yaml

$ cld app show hello-world-1

$ curl <app-url>


===========================
Deploying locally on Mac
===========================

In our testing On Mac (with Docker version 17.06.0-ce, build 02c1d87)
we observed that CloudARK times out while pinging to check if application is up 
even after application container has started successfully. So CloudARK will mark the deployment
as failed. If such a situation happens, try using IP address of the VM which is created by Docker-for-Mac
to access the application URL. For instance,

curl http://192.168.99.100:<port>/

You can find out IP of VM by executing following command: docker-machine ip default

You can find the port from the 'url' attribute that is available from output of command:

$ cld app show <app-name>

We have an open issue (https://github.com/cloud-ark/cloudark/issues/146) to address this bug.


=====================
Deploying on AWS ECS
=====================

$ cld env create env-aws environment-ecs.yaml

$ cld container create cont2 ecr

Edit app.yaml to include image uri (tagged_image attribute value) obtained from output of command:

$ cld container show cont2

$ cld app deploy hello-world-2 env-aws app.yaml

$ cld app show hello-world-2

$ curl <app_url>


========================
Deploying on Google GKE
========================

$ cld env create env-gke environment-gke.yaml

$ cld container create cont3 gcr --project-id <ID of you GCloud project>

Edit app.yaml to include image uri obtained from output of command:

$ cld container show cont3

$ cld app deploy hello-world-3 env-gke app.yaml

$ cld app show hello-world-3

$ curl <app_url>



Track / Debug:
---------------

$ cld env show <env-name>

$ cld app show <app-name>

$ cld app logs <app-name>

$ cld env shell <env-name>


Verify:
-------

$ cld app show <app-name>

$ cld app list

$ cld env show <env-name>

$ cld env list


Cleanup:
--------

$ cld app delete <app-name>

$ cld env delete <env-name>

$ cld container delete <container-name>

