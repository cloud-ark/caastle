Sample Deployments
-------------------

Check this `repository`_ to see examples of deploying applications using CloudARK.

.. _repository: https://github.com/cloud-ark/cloudark-samples



Some typical workflows using CloudARK are presented below:

**1) Developer workflow when developing locally:**

Suppose the application is a single container application and needs MySQL for backend.

1) Write application code

2) Create application-specific artifacts:

   - Dockerfile_

.. _Dockerfile: https://github.com/cloud-ark/cloudark-samples/blob/master/greetings/Dockerfile

   - `env definition file (env.yaml)`__

.. _env: https://github.com/cloud-ark/cloudark-samples/blob/master/greetings/environment-local.yaml

__ env_

   - `app definition file (app.yaml)`__

.. _app: https://github.com/cloud-ark/cloudark-samples/blob/master/greetings/app-local.yaml

__ app_

   Ensure that app.yaml includes `interpolated variables`__ corresponding to the environment variables that should be bound to cloud resources in the environment

.. _interpolation: https://cloud-ark.github.io/cloudark/docs/html/html/env_vars.html

__ interpolation_

3) Create local environment: cld env create localenv env.yaml

4) Create container: cld container create cont1 local

5) Edit app.yaml to include image id obtained from output of 'cld container show cont1' command

6) Deploy application: cld app deploy app1 localenv app.yaml

7) Test and modify application code

8) Create new container: cld container create cont2 local

9) Edit app.yaml to include image id obtained from output of 'cld container show cont2' command

10) Deploy application: cld app deploy app2 localenv app.yaml

11) Cleanup:

    - cld container delete cont1

    - cld app delete app1

    - cld container delete cont2

    - cld app delete app2

    - cld env delete localenv


**2) Developer workflow to test application on Public cloud:**

Suppose your deployment target is Google cloud.

1) Modify env.yaml to include Google cloud resources (cloudsql and gke)

2) Create environment: cld env create testenv1 env.yaml

3) Create container: cld container create gkecont gcr

4) Edit app.yaml to include image uri obtained from output of 'cld container show gkecont' command

5) Deploy application: cld app deploy gkeapp testenv1 app.yaml

6) Test the application

7) Open environment-specific shell: cld env shell testenv1

8) Execute kubectl commands in the shell to verify that pods and services are working as expected:
   
   - kubectl get pods

   - kubectl get services

   - kubectl logs <pod-name>

9) Execute gcloud commands in the shell to verify that Cloud SQL was provisioned correctly:
   
   - gcloud sql instances list

   - gcloud sql instances describe <instance-name>

10) Check-in following application artifacts to source control: env.yaml, app.yaml


**3) Operator workflow to perform staging/production deployments:**

1) Create staging-env.yaml with appropriate resource attributes

2) Create staging environment: cld env create staging staging-env.yaml

3) Take app.yaml available in source control. There is no need to edit it as the container
   image uri that should be used for deployment is already defined in app.yaml

4) Deploy application on staging environment: cld app deploy app1 staging app.yaml

5) Get application URL and IP address from output of: cld app show app1

6) Verify that app1 is working as expected

7) Get application deployment and runtime logs for inspection: cld app logs app1

8) Create production-env.yaml with appropriate resource attributes

9) Create production environment: cld env create production production-env.yaml

10) Deploy application on production environment: cld app deploy prodapp production app.yaml

11) Get application URL and IP address from output of: cld app show prodapp

12) Update application's canonical DNS entry to point to IP address of prodapp


Videos:
--------

1) CloudARK setup: https://youtu.be/88kClIy8qp4


2) Wordpress deployment on GKE: https://youtu.be/c7pO7TO0KzU
