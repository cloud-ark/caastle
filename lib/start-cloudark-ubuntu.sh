#!/bin/bash

install_log="install.log"
touch $install_log

virtenv="cloudark-virtenv"
source $virtenv/bin/activate &>> $install_log

./$virtenv/bin/python server/setup.py install
./$virtenv/bin/python server/fmserver.py 1>>cld.log 2>&1 &

# Delete previous error file

if [[ -f "cloudark.error" ]]; then
   rm -f "cloudark.error"
fi 

while [[ ! -f "cloudark.status" ]]
do
  echo "Waiting for CloudARK server to start"
  sleep 5s
  if [[ -f "cloudark.error" ]]; then
      echo "Error occurred in starting CloudARK server. Check cloudark.error"
      exit
  fi
done

sleep 1s

if [[ -f "cloudark.status" ]]; then
    echo "CloudARK server successfully started."
    echo "Next steps:"
    echo "- Run 'cld --help' to see available commands"
    echo "- Quick test: Run 'cld app list'"
    echo "- Try sample programs from cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)"
fi

#/bin/bash -c ". $virtenv/bin/activate; exec /bin/bash -i"
