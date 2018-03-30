Wordpress
----------


Deploy on GKE
--------------

$ cld env create gke-env environment-cloudsql-gke.yaml

$ cld container create cont1 gcr

Edit app-gke.yaml to include image url obtained from output of:

$ cld container show cont1 

$ cld app deploy wpgke gke-env app-gke.yaml

$ cld app show wpgke

$ cld env shell gke-env

  > help
  > kubectl get services
  > kubectl get pods
  > kubectl logs <pod-name>
  > gcloud sql instances list
  > gcloud sql instances describe <instance-name>
  > exit



Deploy on ECS
--------------

Screenshots of wordpress deployment of ECS available in the README at: https://github.com/cloud-ark/cloudark

$ cld env create ecs-env environment-rds-ecs.yaml

$ cld container create cont2 ecr

Edit app-ecs.yaml to include image url obtained from output of:

$ cld container show cont2

$ cld app deploy wpecs ecs-env app-ecs.yaml

$ cld env shell ecs-env

  > help


Track / Debug:
---------------

$ cld env show <env-name>

$ cld app show <app-name>

$ cld app logs <app-name>

$ cld env shell <env-name>


Cleanup:
---------
$ cld app delete <app-name>

$ cld env delete <env-name>


Verify:
-------

$ cld app show <app-name>

$ cld app list

$ cld env show <env-name>

$ cld env list

