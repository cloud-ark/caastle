#!/bin/bash

# define installation log file
truncate -s 0 install.log
install_log="install.log"
echo "Installing CloudARK. Installation logs stored in $install_log" 

virtenv="cloudark-virtenv"
virtenvbin=`pwd`/$virtenv/bin
echo "Creating virtual environment $virtenv" &>> $install_log
virtualenv $virtenv &>> $install_log
source $virtenv/bin/activate &>> $install_log

pip install -r requirements.txt &>> $install_log
./$virtenv/bin/python server/setup.py install

cd client
../$virtenv/bin/python setup.py install &>> $install_log

[[ ":$PATH:" != *":`pwd`:"* ]] && PATH="`pwd`:${PATH}"
[[ ":$PATH:" != *":$virtenvbin:"* ]] && PATH="$virtenvbin:${PATH}"
echo '### Added by CloudARK' >> ~/.profile
echo "export PATH=$PATH" >> ~/.profile
echo '### Added by CloudARK' >> ~/.bashrc
echo "export PATH=$PATH" >> ~/.bashrc

[[ ":$PYTHONPATH:" != *":`pwd`:"* ]] && PYTHONPATH="`pwd`:${PYTHONPATH}"
[[ ":$PYTHONPATH:" != *":$virtenvbin:"* ]] && PYTHONPATH="$virtenvbin:${PYTHONPATH}"
echo '### Added by CloudARK' >> ~/.profile
echo "export PYTHONPATH=$PYTHONPATH" >> ~/.profile
echo '### Added by CloudARK' >> ~/.bashrc
echo "export PYTHONPATH=$PYTHONPATH" >> ~/.bashrc

echo "Installing cloudark client done." &>> $install_log

cd ..
echo "Starting server.." &>> $install_log
ps -eaf | grep 'python server/fmserver.py' | grep -v grep | awk '{print $2}' | xargs kill &>> $install_log
python server/fmserver.py 1>>cld-server.log 2>&1 &

has_server_started=`ps -eaf | grep fmserver` 

if [[ ! -z "${has_server_started}" ]]; then
    echo "CloudARK successfully installed."
    echo "Next steps:"
    echo "- Quick test: Run 'cld --help'"
    echo "- Try sample programs from cloudark-samples repository (https://github.com/cloud-ark/cloudark-samples.git)"
fi


# Activate virtual environment
/bin/bash -c ". $virtenv/bin/activate; exec /bin/bash -i"



