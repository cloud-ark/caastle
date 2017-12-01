#!/bin/bash

# Check if the platform is one that we support
declare -a supported_platform_list=("Ubuntu 14.04", "Ubuntu 16.04", "OS X - Darwin");
platform=`uname -a | grep -E "Ubuntu|Darwin"`

if [[ -z "$platform" ]]; then
   echo "Unsupported platform. Currently supported platforms: ${supported_platform_list[@]}"
   exit
fi

if [[ -f "cloudark.status" ]]; then
   echo "Removing previous cloudark.status file"
fi

host_platform=`uname -a | awk '{print $4}'`

if [ "$host_platform" = "Darwin" ]; then
   echo "Host OS: Mac OS X"
   source lib/start-cloudark-mac.sh
elif [[ "$host_platform" =~ "Ubuntu" ]]; then
   echo "Host OS: Ubuntu"
   source lib/start-cloudark-ubuntu.sh
else
   echo "Unknown platform"
fi
