#!/bin/bash

VSWARM_FOLDER=$HOME/vSwarm/tools/invoker

# Define variables
PORT=80
DEBUG_FLAG="false"
TIME=900
RPS=800
STATISTICS_INTERVAL=30000

FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
mkdir -p $FOLDER

cp $VSWARM_FOLDER/cleandatfiles.sh $FOLDER/cleanfiles.sh
chmod +x $FOLDER/cleanfiles.sh

RESULTS_FILE="$FOLDER/invoke_functions.dat"
PERF_FILE="$FOLDER/perf.dat"
MPSTAT_FILE="$FOLDER/mpstat.dat"
OUTPUT_JSON_FILE="$FOLDER/output.json"
OUTPUT_PNG_FILE=$FOLDER


# Run the command
cd $VSWARM_FOLDER
python3 collect_endpoints.py
make invoker
sudo ./invoker -port $PORT -time $TIME -rps $RPS -dbg=$DEBUG_FLAG -perf=$PERF_FILE -mpstat=$MPSTAT_FILE -statinterval=$STATISTICS_INTERVAL > $RESULTS_FILE
python3 ./statanalysis.py $PERF_FILE $MPSTAT_FILE $RESULTS_FILE $OUTPUT_JSON_FILE $TIME
python3 ./plotstatanalysis.py $OUTPUT_JSON_FILE $OUTPUT_PNG_FILE
$VSWARM_FOLDER/cleandatfiles.sh
