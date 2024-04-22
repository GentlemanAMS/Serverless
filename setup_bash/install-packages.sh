#!/bin/bash

source $HOME/.bashrc
source /etc/profile

sudo apt-get update
sudo apt-get upgrade -y

sudo apt-get install -y htop
echo "HTOP Installed"

sudo apt install -y linux-tools-common linux-tools-generic linux-cloud-tools-generic
sudo apt install -y linux-tools-$(uname -r) linux-cloud-tools-$(uname -r)
echo "Perf Tools Installed"

sudo apt install -y sysstat
echo "MPStat Installed"

sudo apt install -y python3-pip
pip install matplotlib
pip install psutil
echo "Installing matplotlib"

pip install scipy
echo "Installing scipy"

pip install colorlog
echo "Color Logging Installed"

sudo apt install --yes jq
echo "Installing jq to process json"
