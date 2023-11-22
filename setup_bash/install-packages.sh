#!/bin/bash

source ~/.bashrc
source /etc/profile

sudo apt-get installed htop
echo "HTOP Installed"

sudo apt install linux-tools-common linux-tools-generic linux-cloud-tools-generic
sudo apt install linux-tools-$(uname -r) linux-cloud-tools-$(uname -r)
echo "Perf Tools Installed"

sudo apt install python3-pip
pip install matplotlib
echo "Installing matplotlib"
