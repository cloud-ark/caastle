

Application type support matrix
--------------------------------

Following table shows currently supported application types, application definition formats, and the target COEs. 

+---------------------------------+-------------------------------+--------------+------------------------------+
| Type                            | Application definition format |   COE        |            Example           |
+=================================+===============================+==============+==============================+
| Single container                | app yaml (CloudARK format)    | ECS & GKE    |         hello-world_         |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Single cont + managed service   | app yaml (CloudARK format)    | ECS & GKE    |         wordpress_           |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Single cont + managed service   | pod yaml (Kubernetes format)  |    GKE       |         greetings_           |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Multi-container                 | pod yaml (Kubernetes format)  |    GKE       |   wordpress_kubernetes_pods_ |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Multi-container + managed serv  | pod yaml (Kubernetes format)  |    GKE       |                              |
+---------------------------------+-------------------------------+--------------+------------------------------+

Upcoming: Multi-container application on AWS (based on ECS Fargate or EKS)


.. _hello-world: https://github.com/cloud-ark/cloudark-samples/tree/master/hello-world

.. _greetings: https://github.com/cloud-ark/cloudark-samples/tree/master/greetings

.. _wordpress: https://github.com/cloud-ark/cloudark-samples/tree/master/wordpress/php5.6/apache

.. _wordpress_kubernetes_pods: https://github.com/cloud-ark/cloudark-samples/tree/master/wordpress-kubernetes-pods



Demo Videos
-----------

1) CloudARK setup: https://youtu.be/88kClIy8qp4


2) Wordpress deployment on GKE: https://youtu.be/c7pO7TO0KzU

