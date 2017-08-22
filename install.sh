#!/bin/bash

# Check if running as root -- if so, exit
if (( $EUID == 0 )); then
   echo "Looks like you are trying to run install.sh as root."
   echo "That is not required actually."
   echo "Just run ./install.sh as regular user."
   exit
fi

# Check if the platform is one that we support
declare -a supported_platform_list=("Ubuntu 14.04", "Ubuntu 16.04", "OS X - Darwin");
platform=`uname -a | grep -E "Ubuntu|Darwin"`

if [[ -z "$platform" ]]; then
   echo "Unsupported platform. Currently supported platforms: ${supported_platform_list[@]}"
   exit
fi

host_platform=`uname -a | awk '{print $4}'`

if [ "$host_platform" = "Darwin" ]; then
   echo "Host OS: Mac OS X"
   source lib/install-mac.sh
elif [[ "$host_platform" =~ "Ubuntu" ]]; then
   echo "Host OS: Ubuntu"
   source lib/install-ubuntu.sh
else
   echo "Unknown platform"
fi
