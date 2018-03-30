JavaScript + REST API
----------------------

This example shows how a web application that uses HTML+JavaScript frontend
and Java REST API can be deployed using CloudARK.

The Dockerfile defines the application build steps.

Three environment yaml files are available in the folder:
a) environment-local.yaml should be used for local deployment
b) environment-ecs.yaml should be used for AWS ECS deployment
e) environment-gke.yaml - for deployments on Google Container Engine (GKE)


===============
Deploy Locally
===============

$ cld env create envlocal environment-local.yaml

$ cld env show envlocal (wait till the status is 'available')

$ cld container create container1 local

$ cld container show container1

Edit app-local.yaml to include image id obtained from output of
cld container show 

$ cld app deploy jsapp1 envlocal app-local.yaml

$ cld app show jsapp1

$ curl <app-url>/test.html

$ curl <app-url>/ajaxexample.html

  Open browser to point to above urls and experiment

$ cld app logs jsapp1

$ cld app delete jsapp1


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


$ curl http://192.168.99.100:<port>/test.html

  Open browser to point to above url

$ curl http://192.168.99.100:<port>/ajaxexample.html

  Open browser to point to above url


=====================
Deploying on AWS ECS
=====================

$ cld env create envaws environment-ecs.yaml

$ cld env show envaws (wait till the status is 'available')

$ cld container create container2 ecr

$ cld container show container2

Edit app-aws.yaml to include image url obtained from output of
cld container show

$ cld app deploy jsapp2 envaws app-aws.yaml

$ cld app show jsapp2

$ curl <app_ip_url>/test.html

$ curl <app_ip_url>/ajaxexample.html

$ curl <app_url>/test.html

$ curl <app_url>/ajaxexample.html

  Open browser and test above urls

$ cld app logs jsapp2

$ cld app delete jsapp2

$ cld env delete envaws


========================
Deploying on Google GKE
========================

$ cld env create envgke environment-gke.yaml

$ cld env show envgke (wait till the status is 'available')

$ cld container create container3 gcr

$ cld container show container3

Edit app-gke.yaml to include image url obtained from output of
cld container show

$ cld app deploy jsapp3 envgke app-gke.yaml

$ cld app show jsapp3

$ curl <app_url>/test.html

$ curl <app_url>/ajaxexample.html

  Open browser to point to above urls

$ cld app logs jsapp3

$ cld app delete jsapp3

$ cld env delete envgke
