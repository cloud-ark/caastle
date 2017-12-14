Installation
-------------

CloudARK requires Docker to be installed on the Host. Also, the effective user permissions of the shell
in which CloudARK is running needs to be such that docker commands can be invoked without sudo.

**Docker installation on Ubuntu**

You will find detailed Docker installation steps on here_.

.. _here: https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#set-up-the-repository

Here are quick steps:

$ sudo apt-get install apt-transport-https ca-certificates curl software-properties-common

$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

$ sudo apt-key fingerprint 0EBFCD88

$ sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

$ sudo apt-get update

$ sudo apt-get install docker-ce

$ sudo usermod -aG docker $USER

Exit from the shell and open another shell (or Logout and log back in).

Verify that you are able to run docker commands without sudo:

$ docker ps -a


**Docker installation on Mac OS**

Docker for Mac: https://docs.docker.com/docker-for-mac/install/


