#!/bin/bash

# Update and upgrade packages
sudo apt-get update
sudo apt-get upgrade

# clone inVitro repository in home directory
cd $HOME
git clone https://github.com/vhive-serverless/invitro.git

