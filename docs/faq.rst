Frequently Asked Questions
---------------------------

1) How is Platform-as-Code different from Platform-as-a-Service (PaaS)?

Platform-as-Code is a non-hosted implementation of platform functionality. 
There is no private / public hosted central server like PaaSes. 
This approach helps improve dev/prod parity and ability to recreate application environments anywhere.

2) How is Platform-as-Code different from Infrastructure-as-Code?

Infrastructure-as-Code implementation treats every platform element as infrastructure resource. 
In contrast, Platform-as-Code offers application centric abstractions that simplify modeling a deployment as per the application architecture.

3) Where does CloudARK store its internal state?

CloudARK stores its internal state in the home folder inside .cld directory.
The database state is stored in ~/.cld/data/deployments/cld.sqlite
Environment, Container, and Application related creation files are stored in separate directories
inside ~/.cld/data/deployments.
You can view all the artifacts that CloudARK generates for each platform element inside
the corresponding directory.

Moreover, CloudARK aims to be a *soft state* system. There is no restriction if you want to 
directly modify any platform element provisioned by CloudARK through the corresponding Cloud's web console.
In the future releases of CloudARK, the internal state will be synced with the state of platform elements on the Cloud.

4) What is environment-specific shell in CloudARK?

CloudARK provides *cld env shell* command that can be used to get a *environment-specific* shell.
This shell allows you to execute cloud-native cli commands corresponding to the platform elements in *that* environment.
This shell can be quite handy when you are developing applications using CloudARK.

5) How does CloudARK strike balance between high-level abstractions and providing control when needed?

There is always fine line between abstraction and control. CloudARK tries to balance these competing goals through
following three aspects of its design:

- For defining platform elements in environment yaml file, CloudARK plans to support all the attributes that
  the corresponding Cloud resource exposes. For the platform elements that are currently supported in CloudARK - AWS RDS,
  AWS ECS, Google Cloud SQL, Google GKE - limited set of attributes are supported in the yaml file. But we will be
  supporting all the setable attributes soon. (In the mean time if you are interested in any particular attribute,
  file a Github issue (https://github.com/cloud-ark/cloudark/issues) and we will add it to CloudARK).

- For microservices definition we take a two pronged approach. For applications that involve a single container, we
  support a simpler application definition format. This format supports minimal set of attributes that are required
  to deploy the single container application. These include, *image uri*, *container_port*, *host_port*, *environment
  variables*. For multi-container applications we support Kubernetes's native yaml file. You can define your Pods, Services, Deployments,
  ReplicationControllers, etc. in Kubernetes's standard format. Currently we require you to define a single file
  containing all your Kubernetes element definitions.

- We provide the mechanism of environment-specific shell (see above) through which you can execute native commands.
  For instance, when developing/deploying your applications on GKE, you might want to execute "kubectl get pods" to
  see if your application's Pods have started up on the GKE cluster. Or you might want to execute "kubectl describe pods <podname>"
  to see what caused Pod from not starting up. The environment-specific shell allows you to execute all such commands
  *without* having to worry about obtaining GKE cluster credentials and setting up kubectl to use them.

6) What kind of application logs CloudARK collects?








 
