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
echo "If Shell is not BASH i.e., /bin/bash - Change the terminal\n\n"


# Setting up oh-my-bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ohmybash/oh-my-bash/master/tools/install.sh)"
source ~/.bashrc

cd $HOME && git clone https://github.com/powerline/fonts.git
cd $HOME/fonts && ./install.sh && cd $HOME
rm -rf $HOME/fonts

echo "Edit OS_THEME in ~/.bashrc to agnoster"
echo "In host computer change the font to Meslo LG M DZ for Powerline Regular: 10"

# sudo apt-get install gawk git gmake
# git clone --recursive --depth 1 --shallow-submodules https://github.com/akinomyoga/ble.sh.git
# make -C ble.sh install PREFIX=~/.local
# echo 'source ~/.local/share/blesh/ble.sh' >> ~/.bashrc
# bind 'set show-all-if-ambiguous on'
# bind 'TAB:menu-complete'

