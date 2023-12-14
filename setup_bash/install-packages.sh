#!/bin/bash

source $HOME/.bashrc
source /etc/profile

sudo apt-get update
sudo apt-get upgrade

sudo apt-get install htop
echo "HTOP Installed"

sudo apt install linux-tools-common linux-tools-generic linux-cloud-tools-generic
sudo apt install linux-tools-$(uname -r) linux-cloud-tools-$(uname -r)
echo "Perf Tools Installed"

sudo apt install sysstat
echo "MPStat Installed"

sudo apt install python3-pip
pip install matplotlib
pip install psutil
echo "Installing matplotlib"

sudo apt install jq
echo "Installing jq to process json"
