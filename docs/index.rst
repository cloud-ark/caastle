.. CloudARK documentation master file, created by
   sphinx-quickstart on Wed Aug 30 10:11:27 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CaaStle's documentation
====================================

CaaStle is a Full-stack microservices development and deployment tool for Google Kubernetes Engine and Amazon Elastic Container Service.

CaaStle makes it easy to develop and deploy microservices that use managed services such as Google Cloud SQL and Amazon RDS.

CaaStle is implemented following the principles of Platform-as-Code paradigm. 

Blog article about Platform-as-Code paradigm:

https://medium.com/@cloudark/introducing-platform-as-code-b6677c699b4

Platform-as-Code paradigm offers ability to define all platform elements of a containerized cloud application using declarative configuration files.
Such declarative platform definitions can be version controlled, shared, analyzed. This simplifies the task of developing microservice based applications

There are two main abstractions in CaaStle - *Environment* and *Application*.


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   environment
   application
   env_vars
   architecture
   deployments
   cli
   faq
   roadmap
   samples
   troubleshooting

..   intro
..   architecture


