#!/bin/bash

source ~/.bashrc
source /etc/profile

cd $HOME/vhive

# Run the node setup script
# To enable runs with stargz images, setup kubelet by adding the stock-only and use-stargz flags
./setup_tool setup_node stock-only use-stargz

# screen is a terminal multiplexer similar to tmux
# screen -dmS containerd containerd: Starts a screen session in detached mode (-dmS), names the session containerd, and then runs the containerd command within that session.
sudo screen -dmS containerd containerd; sleep 5;

# NOTE: When you are running single node cluster as stock-only
# DO NOT start firecracker-containerd
# DO NOT start vHive in a background terminal named vhive

# Run the single node cluster setup script
./setup_tool create_one_node_cluster stock-only


# Copying files from benchmarks to vSwarm/tools/invoke: TO BE TESTED
cp $HOME/benchmarking/collect_endpoints.py $HOME/vSwarm/tools/invoke/
cp $HOME/benchmarking/invoke_functions.sh $HOME/vSwarm/tools/invoke/
cp $HOME/benchmarking/client.go $HOME/vSwarm/tools/invoke/
echo "Copying necessary files"

# Build invoker: TO BE TESTED
cd $HOME/vSwarm/tools/invoke/
make invoker
echo "Building invoker"


# Wait for all the containers to boot up:
watch kubectl get pods -A
