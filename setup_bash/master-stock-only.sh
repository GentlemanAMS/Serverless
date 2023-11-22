#!/bin/bash

source ~/.bashrc
source /etc/profile

cd $HOME/vhive

# Run the node setup script
# To enable runs with stargz images, setup kubelet by adding the stock-only and use-stargz flags
./setup_tool setup_node stock-only use-stargz

# Start containerd in a background terminal named containerd
# screen is a terminal multiplexer similar to tmux
# screen -dmS containerd containerd: Starts a screen session in detached mode (-dmS), names the session containerd, and then runs the containerd command within that session.
sudo screen -dmS containerd bash -c "containerd > >(tee -a /tmp/vhive-logs/containerd.stdout) 2> >(tee -a /tmp/vhive-logs/containerd.stderr >&2)"


# Run the multi node cluster setup script
./setup_tool create_multinode_cluster stock-only

