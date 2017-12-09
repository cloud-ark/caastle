.. CloudARK documentation master file, created by
   sphinx-quickstart on Wed Aug 30 10:11:27 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CloudARK's documentation
====================================

Platform of an application is defined as the run-time environment in which the application runs. It includes application code, application servers, and application’s external resource dependencies such as databases.

In case of a containerized cloud application, platform elements generally include:

- Application container/s

- Container orchestration engine cluster

- Required managed cloud services like database-as-a-service, load balancers etc.

Platform-as-Code paradigm offers ability to define all platform elements of a containerized cloud application using declarative configuration files. These platform definitions can be version controlled and follow software development lifecycle. Refer to our free whitepaper_ for more about Platform-as-Code (PaC) paradigm.
CloudARK is an implementation of Platform-as-Code (PaC) paradigm.

.. _whitepaper:  https://cloudark.io/resources

CloudARK is implementation of Platform-as-Code (PaC) paradigm.

There are two main abstractions in CloudARK - *Environment* and *Application*.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   environment
   application
   env_vars
   deployments
   architecture
   faq
   roadmap


..   intro
..   architecture


