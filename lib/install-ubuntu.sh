#!/bin/bash

# define installation log file
truncate -s 0 install.log
install_log="install.log"
echo "Installing CloudARK. Installation logs stored in $install_log" 

sudo apt-get update && sudo apt-get install -y python-pip
sudo pip install virtualenv

virtenv="cloudark-virtenv"
virtenvbin=`pwd`/$virtenv/bin
echo "Creating virtual environment $virtenv" &>> $install_log
virtualenv $virtenv &>> $install_log
source $virtenv/bin/activate &>> $install_log

pip install -r requirements.txt &>> $install_log

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

echo "Installing CloudARK client done." &>> $install_log

cd ..

echo "Next steps:"
echo "- Run 'cld --help' to see available commands"
echo "- Do cloud setup using: "
echo "  - cld setup aws - to do aws setup"
echo "  - cld setup gcloud - to do gcloud setup"
echo "- Once required cloud setup is done, start CloudARK server"
echo "  - ./start-cloudark.sh"

# Activate virtual environment
#/bin/bash -c ". $virtenv/bin/activate; exec /bin/bash -i"



