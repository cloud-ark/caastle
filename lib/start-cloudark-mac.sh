#!/bin/bash

install_log="install.log"
touch $install_log

virtenv="cloudark-virtenv"
source $virtenv/bin/activate >> $install_log

./$virtenv/bin/python server/setup.py install
./$virtenv/bin/python server/fmserver.py 1>>cld.log 2>&1 &

sleep 5s

has_server_started=`ps -eaf | grep fmserver` 

if [[ ! -z "${has_server_started}" ]]; then
    echo "CloudARK server successfully started."
    echo "Next steps:"
    echo "- Quick test: Run 'cld app list'"
    echo "- Try sample programs from cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)"
fi
