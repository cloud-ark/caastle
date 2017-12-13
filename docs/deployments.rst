Cloud Setup
------------

Before you start using CloudARK, you will need to do the appropriate cloud setup as explained in
following sections. This setup allows CloudARK to make required calls to the target cloud
as part of creating an environment and deploying an application.


Google Setup
-------------

$ cld setup gcloud

This will request OAuth authorizations for gcloud sdk and gcloud auth library. Follow the prompts and provide the required input.

$ ./restart-cloudark.sh

Create a project from Google Cloud console. Note down the Project ID.
You will need to pass it when creating container to be saved in GCR and when
creating GKE environment.


Amazon Setup
-------------

$ cld setup aws
    
This will prompt you to enter AWS access_key_id, secret_access_key, region, output format.
Follow the prompts and provide the required input.

$ ./restart-cloudark.sh


Your AWS user will need to have following managed policies in order to do deployments using CloudARK.

- AmazonEC2FullAccess
- AmazonEC2ContainerRegistryFullAccess
- AmazonEC2ContainerServiceFullAccess
- AmazonEC2ContainerServiceAutoscaleRole
- AmazonEC2ContainerServiceforEC2Role
- AmazonRDSFullAccess (if your application depends on RDS)

Additionally your AWS user will need to have the EC2 Container Service Role. Use these steps to create it:

-> AWS Web Console -> IAM -> Roles -> Create Role -> Select EC2 Container Service -> In "Select your use case" choose EC2 Container Service 
-> Next: Permissions -> Next: Review -> For role name give "EcsServiceRole" -> Hit "Create Role".

Finally you will also need to add IAM policy shown below which will grant permissions to the
ECS agent running on your ECS cluster instances to perform IAM actions
such as creating a ECS instance profile role and assuming that role.
This is required for the ECS agent to communicate with the ECS service.
Use these steps to create this policy:

-> AWS Web Console -> IAM -> Select your user in IAM -> Add permissions -> Attach existing policies directly -> Create Policy
-> Create Your Own Policy

In the Policy Document enter following policy. Replace <account-id> with your account id.

::

  {
      "Version": "2012-10-17",
      "Statement": [
          {
              "Effect": "Allow",
              "Action": "iam:*",
              "Resource": ["arn:aws:iam::<account-id>:role/*",
                           "arn:aws:iam::<account-id>:instance-profile/*]"
          }
      ]
  }

Once the policy is created attach it to your user.


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



