Hello World (Servlet)
----------------------

This example shows how a web application written using Java Servlets
can be deployed using CloudARK.

There are two environment yaml files available in the folder:
a) environment-local.yaml should be used for local deployment
b) environment-ecs.yaml should be used for AWS ECS deployment
b) environment-gke.yaml should be used for GKE deployment

==================
Deploying locally
==================

$ cld container create cont1 local-docker

Edit app.yaml to include image id obtained from command:

$ cld container show cont1

$ cld env create env1 environment-local.yaml

$ cld app deploy servlet-app env1 app.yaml

$ curl http://localhost:<port>/hello-world-servlet/

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

