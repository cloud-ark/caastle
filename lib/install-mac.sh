#!/bin/bash

brew update
brew install openssl
brew install python --with-brewed-openssl

# define installation log file
rm -rf install.log
touch install.log
install_log="install.log"
echo "Installing CloudARK. Installation logs stored in $install_log"

echo "Checking if Docker is installed or not.."

docker_available=`docker ps | grep "CONTAINER ID"`

if [[ -z "$docker_available" ]]; then
   echo "Docker is not installed. Please install Docker and then run install.sh again."
   echo "https://cloud-ark.github.io/cloudark/docs/html/html/installation.html"
   exit
fi

curl -O http://python-distribute.org/distribute_setup.py
python distribute_setup.py
curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
python get-pip.py

sudo pip install virtualenv


virtenv="cloudark-virtenv"
virtenvbin=`pwd`/$virtenv/bin
echo "Creating virtual environment $virtenv" >> $install_log
virtualenv -p /usr/local/Cellar/python/2.7.14/bin/python2 $virtenv >> $install_log
source $virtenv/bin/activate >> $install_log

pip install -r requirements.txt >> $install_log

cd client
../$virtenv/bin/python setup.py install >> $install_log

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

echo "Installing CloudARK client done." >> $install_log

cd ..

echo "Next steps:"
echo "1) Do cloud setup using: "
echo "   $ cld setup aws - to do aws setup"
echo "   $ cld setup gcloud - to do gcloud setup"
echo "2) Start cloudark server"
echo "   $ ./start-cloudark.sh"

# Activate virtual environment
/bin/bash -c ". $virtenv/bin/activate; exec /bin/bash -i"



