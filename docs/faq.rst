Frequently Asked Questions (FAQ)
---------------------------------

Q) **How is Platform-as-Code (PaC) different from Platform-as-a-Service (PaaS)?**

Platform-as-Code is a non-hosted implementation of platform functionality. 
There is no private / public hosted central server like PaaSes. 
This approach helps improve dev/prod parity and ability to recreate application environments anywhere.


Q) **How is Platform-as-Code (PaC) different from Infrastructure-as-Code (IaC)?**

Infrastructure-as-Code implementation treats every platform element as infrastructure resource. 
In contrast, Platform-as-Code offers application-centric abstractions that simplify modeling a deployment as per the application architecture.


Q) **How does Platform-as-Code (PaC) approach compare with language-based deployment approach of Metaparticle**?

Metaparticle_ provides cloud deployment primitives that can be integrated directly within an application's code.
It is essentially a reusable deployment library.
Platform-as-Code (PaC) approach is language neutral. It provides high-level abstractions for defining the
entire stack of a containerized cloud application. It leverages popular declarative definition formats such as Kubernetes yaml format for application definition.

.. _Metaparticle: https://metaparticle.io/


Q) **How does CaaStle strike balance between high-level abstractions and providing control when needed?**

CaaStle tries to balance the fine line between abstraction and control through following three aspects of its design:

- First, for defining platform elements in environment yaml file, CaaStle plans to support all the attributes that
  the corresponding cloud resource exposes. For the platform elements that are currently supported in CaaStle - AWS RDS,
  AWS ECS, Google Cloud SQL, Google GKE - limited set of attributes are supported in the yaml file. But we will be
  supporting all the settable attributes soon. (In the mean time if you are interested in any particular attribute,
  file a Github issue_ and we will add it to CaaStle).

.. _issue: https://github.com/cloud-ark/cloudark/issues


- Second, for microservices definition we take a two pronged approach. For applications that involve a single container, we
  support a simple application definition format that supports minimal set of attributes which would be typically used
  to deploy such applications. These attributes include, *image uri*, *container_port*, *host_port*, *environment
  variables*. For multi-container applications we support Kubernetes's native yaml file. You can define your container Pods
  in Kubernetes's standard format. We require you to define `a single file containing all your Pod definitions`__ in it.

.. _podsonly: https://github.com/cloud-ark/cloudark/issues/200

__ podsonly_

- Third, we provide the mechanism of *environment-specific shell* (see below) through which you can execute native commands specific to the resources in the environment.
  For instance, when developing/deploying your applications on GKE, you might want to execute "kubectl get pods" to
  see if your application's Pods have started up on the GKE cluster. Or you might want to execute "kubectl describe pods <podname>"
  to see what caused a Pod from not starting up. The environment-specific shell allows you to execute all such commands
  *without* requiring you to `install and setup cloud CLIs on your machines`__.

.. _arch: https://cloud-ark.github.io/cloudark/docs/html/html/architecture.html

__ arch_


Q) **What is environment-specific shell in CaaStle?**

CaaStle provides *cld env shell* command that can be used to get a *environment-specific* shell.
This shell allows you to execute cloud-native CLI commands corresponding to the platform elements in *that* environment, e.g. 'gcloud sql', 'aws rds', 'kubectl', etc. 
This shell can be quite handy when you are developing applications using CaaStle.
It offers a great tool for traceability without having to setup number of CLI tools.


Q) **Who are the target users of CaaStle?**

Development teams developing containerized cloud applications that run on public clouds like AWS or Google cloud.


Q) **What are the typical use-cases of CaaStle?**

CaaStle is targeted as a common tool between developers and operations engineers.
CaaStle provides easy way for developers and ops to collaborate on declarative platform definitions.
Developers can use CaaStle as local development environment, along with Docker.
Ops engineers can integrate CaaStle-based application deployment workflow in their standard Jenkins like DevOps workflow.
CaaStle's features of application-centric shell, full-stack platform elements association view,
and environment change history (upcoming) are useful for developers and ops engineers alike when
debugging application behaviors or managing environments.


Q) **How does CaaStle differ from Infrastructure-as-Code tools such as Terraform or AWS CloudFormation?**


CaaStle provides application-centric abstractions whereas IaC tools work with infrastructure abstractions.


Q) **How does CaaStle differ from cloud native PaaSes like AWS Elastic Beanstalk or Google App Engine?**

CaaStle is a non-hosted implementation of platform functionality. It integrates with Cloud-based
container orchestration engine systems directly from your laptop. PaaSes introduce an additional hosted indirection which makes them opaque for application developers.



