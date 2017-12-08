Deployment to GKE
------------------

$ cld setup gcloud

This will request OAuth authorizations for gcloud sdk and gcloud auth library. Follow the prompts and provide the required input.

$ ./restart-cloudark.sh

Create a project from Google Cloud console. Note down the Project ID.
You will need to pass it when creating container to be saved in GCR and when
creating GKE environment.


Deployment to Amazon ECS
-------------------------

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


.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :hidden:

   architecture
   faq
   roadmap

