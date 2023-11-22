#!/bin/bash

VSWARM_FOLDER=$HOME/vSwarm/tools/invoker

FOLDER=$VSWARM_FOLDER

# Define variables
PORT=80
DEBUG_FLAG="false"
TIME=900
RPS=5

# Run the command
cd $VSWARM_FOLDER
python3 collect_endpoints.py

cp $VSWARM_FOLDER/client.go $VSWARM_FOLDER/temp
cp $VSWARM_FOLDER/client_backup.go $VSWARM_FOLDER/client.go
cp $VSWARM_FOLDER/temp $VSWARM_FOLDER/client_backup.go
rm temp

make invoker

cp $VSWARM_FOLDER/client.go $VSWARM_FOLDER/temp
cp $VSWARM_FOLDER/client_backup.go $VSWARM_FOLDER/client.go
cp $VSWARM_FOLDER/temp $VSWARM_FOLDER/client_backup.go
rm temp

sudo ./invoker -port $PORT -time $TIME -rps $RPS -dbg=$DEBUG_FLAG
$VSWARM_FOLDER/cleandatfiles.sh
