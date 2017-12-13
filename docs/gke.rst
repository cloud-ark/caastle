

Google Setup
-------------

$ cld setup gcloud

This will request OAuth authorizations for gcloud sdk and gcloud auth library. Follow the prompts and provide the required input.

$ ./restart-cloudark.sh

Create a project from Google Cloud console. Note down the Project ID.
You will need to pass it when creating container to be saved in GCR and when
creating GKE environment.

