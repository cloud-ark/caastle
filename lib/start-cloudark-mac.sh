#!/bin/bash

install_log="install.log"
touch $install_log

virtenv="cloudark-virtenv"
#virtenvbin=`pwd`/$virtenv/bin
#echo "Creating virtual environment $virtenv" >> $install_log
#virtualenv $virtenv >> $install_log
source $virtenv/bin/activate >> $install_log

#pip install -r requirements.txt >> $install_log

#cd client
#../$virtenv/bin/python setup.py install >> $install_log

#[[ ":$PATH:" != *":`pwd`:"* ]] && PATH="`pwd`:${PATH}"
#[[ ":$PATH:" != *":$virtenvbin:"* ]] && PATH="$virtenvbin:${PATH}"
#echo '### Added by CloudARK' >> ~/.profile
#echo "export PATH=$PATH" >> ~/.profile
#echo '### Added by CloudARK' >> ~/.bashrc
#echo "export PATH=$PATH" >> ~/.bashrc

#[[ ":$PYTHONPATH:" != *":`pwd`:"* ]] && PYTHONPATH="`pwd`:${PYTHONPATH}"
#[[ ":$PYTHONPATH:" != *":$virtenvbin:"* ]] && PYTHONPATH="$virtenvbin:${PYTHONPATH}"
#echo '### Added by CloudARK' >> ~/.profile
#echo "export PYTHONPATH=$PYTHONPATH" >> ~/.profile
#echo '### Added by CloudARK' >> ~/.bashrc
#echo "export PYTHONPATH=$PYTHONPATH" >> ~/.bashrc

#cd ..

./$virtenv/bin/python server/setup.py install
./$virtenv/bin/python server/fmserver.py 1>>cld.log 2>&1 &

sleep 5s

has_server_started=`ps -eaf | grep fmserver` 

if [[ ! -z "${has_server_started}" ]]; then
    echo "CloudARK successfully installed."
    echo "Next steps:"
    echo "- Quick test: Run 'cld --help'"
    echo "- Try sample programs from cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)"
fi
