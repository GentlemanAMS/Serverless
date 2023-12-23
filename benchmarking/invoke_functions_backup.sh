#!/bin/bash

VSWARM_FOLDER=$HOME/vSwarm/tools/invoker

FOLDER=$VSWARM_FOLDER

# Define variables
PORT=80
DEBUG_FLAG="false"
TIME=300
RPS=5000

# Run the command
cd $VSWARM_FOLDER
python3 collect_endpoints.py

rm ./invoker
make invoker
sudo ./invoker -port $PORT -time $TIME -rps $RPS -dbg=$DEBUG_FLAG
$VSWARM_FOLDER/cleandatfiles.sh
