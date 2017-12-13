
Cloud Authorization Explained
------------------------------

CloudARK uses combination of target cloud's SDKs and CLIs as cloud deployment mechanisms.
The reason for this two-pronged approach is explained in `architecture section`__.

.. _arch: https://cloud-ark.github.io/cloudark/docs/html/html/architecture.html

__ arch_

The deployment mechanism dictates the nature of authorizations needed by CloudARK.

For Google cloud, CloudARK uses the Google cloud SDK, the Google cloud CLI and Kubernetes CLI (kubectl) for performing deployments.
The Google cloud SDK and CLI need separate OAuth authorizations. When you run 'cld setup gcloud' command you will have to
grant authorizations for both. Once the authorizations are granted, the auth information is stored in following directories:

~/.config/gcloud and ~/.kube

These are the standard directories where Google Cloud SDK/CLI and kubectl CLI expect authorization information.

For AWS, authorization based on user's access key is sufficient for both SDK and CLI.
CloudARK uses the access key provided by the user and stores it in ~/.aws directory as part of 'cld setup aws' command.
This is the standard directory in which AWS SDK and AWS CLI look for authorization credentials.
Additionally, CloudARK also generates a ssh key-pair when provisioning cluster instances for an environment.
This key is stored in the environment-specific folder inside ~/.cld/data/deployments/environments directory. This key can be used to login to the ECS cluster instance using following command:

ssh -i "<pem file>" ec2-user@<AWS cluster instance IP>
