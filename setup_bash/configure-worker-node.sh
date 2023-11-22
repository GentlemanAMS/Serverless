#!/bin/bash

source ~/.bashrc
source /etc/profile

cd $HOME/vhive

IP=0
PORT=0
TOKEN=0
TOKEN_HASH=0

sudo kubeadm join $IP:$PORT --token $TOKEN --discovery-token-ca-cert-hash $TOKEN_HASH > >(tee -a /tmp/vhive-logs/kubeadm_join.stdout) 2> >(tee -a /tmp/vhive-logs/kubeadm_join.stderr >&2)

