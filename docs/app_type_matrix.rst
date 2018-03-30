

Application type support matrix
--------------------------------

Following table shows currently supported application types, application definition formats, and the target COEs. 

+---------------------------------+-------------------------------+--------------+------------------------------+
| Type                            | Application definition format |   COE        |            Example           |
+=================================+===============================+==============+==============================+
| Single container                | app yaml (CaaStle format)     | ECS & GKE    |         hello-world_         |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Single cont + managed service   | app yaml (CaaStle format)     | ECS & GKE    |         wordpress_           |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Single cont + managed service   | pod yaml (Kubernetes format)  |    GKE       |         greetings_           |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Multi-container                 | pod yaml (Kubernetes format)  |    GKE       |   wordpress_kubernetes_pods_ |
+---------------------------------+-------------------------------+--------------+------------------------------+
| Multi-container + managed serv  | pod yaml (Kubernetes format)  |    GKE       |                              |
+---------------------------------+-------------------------------+--------------+------------------------------+

Upcoming: Multi-container application on AWS (based on ECS Fargate or EKS)

.. _hello-world: https://github.com/cloud-ark/caastle/tree/master/examples/hello-world

.. _greetings: https://github.com/cloud-ark/caastle/tree/master/examples/greetings

.. _wordpress: https://github.com/cloud-ark/caastle/tree/master/examples/wordpress/php5.6/apache

.. _wordpress_kubernetes_pods: https://github.com/cloud-ark/caastle/tree/master/examples/wordpress-kubernetes-pods



Demo Videos
-----------

1) CaaStle setup: https://youtu.be/88kClIy8qp4


2) Wordpress deployment on GKE: https://youtu.be/c7pO7TO0KzU


3) Wordpress deployment on ECS: https://youtu.be/psgFyCa2PQA
