#!/bin/bash

#This Bash script sets up SSH Connection

# Generate the SSH keys: Not required
#cd $HOME/.ssh/
#ssh-keygen -t rsa -b 4096 -C "arunkrish2603@gmail.com"

# Set the desired ClientAliveInterval and ClientAliveCountMax values
CLIENT_ALIVE_INTERVAL=3
CLIENT_ALIVE_COUNT_MAX=1200

# Backup the original sshd_config file
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config_backup

# Update the sshd_config file with the new values
# Referred to https://www.tutorialspoint.com/how-to-increase-ssh-connection-timeout-in-linux

echo "Set ClientAliveInterval $CLIENT_ALIVE_INTERVAL in /etc/ssh/sshd_config" 
echo "Set ClientAliveCountMax $CLIENT_ALIVE_COUNT_MAX in /etc/ssh/sshd_config" 

# start the SSH agent and add your SSH private key to the agent
eval "$(ssh-agent -s)" && ssh-add

# Restart the SSH service
sudo service ssh restart
sudo systemctl reload sshd
echo "SSH connection timeout settings updated successfully."

