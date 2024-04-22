#!/bin/bash

#This Bash script sets up SSH Connection

# Generate the SSH keys: 
# ssh-keygen -t rsa -b 4096 -C "ee19b001@smail.iitm.ac.in"
# cat ~/.ssh/id_rsa.pub

# Set the desired ClientAliveInterval and ClientAliveCountMax values
CLIENT_ALIVE_INTERVAL=3
CLIENT_ALIVE_COUNT_MAX=1200

# Backup the original sshd_config file
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config_backup

# Update the sshd_config file with the new values
# Referred to https://www.tutorialspoint.com/how-to-increase-ssh-connection-timeout-in-linux

sudo echo "ClientAliveInterval $CLIENT_ALIVE_INTERVAL" >> /etc/ssh/sshd_config
sudo echo "ClientAliveCountMax $CLIENT_ALIVE_COUNT_MAX" >> /etc/ssh/sshd_config

# Restart the SSH service
sudo service ssh restart
sudo systemctl reload sshd
echo "SSH connection timeout settings updated successfully."


# start the SSH agent and add your SSH private key to the agent
eval "$(ssh-agent -s)" && ssh-add


# Print which shell
echo "Shell: $SHELL"
echo "If Shell is not BASH i.e., /bin/bash - Change the terminal"


# Do this at the end after installation of vHive and vSwarm and single node setup

# Setting up oh-my-bash
# bash -c "$(curl -fsSL https://raw.githubusercontent.com/ohmybash/oh-my-bash/master/tools/install.sh)"
# source ~/.bashrc

# echo "Edit OS_THEME in ~/.bashrc to agnoster"
# echo "In host computer change the font to Meslo LG M DZ for Powerline Regular: 10"

# Once this is done, the path variables that are exported previously are not included in the new bashrc file automatically. You should include them by copying the export statements from the backup bashrc file into the new bashrc file

