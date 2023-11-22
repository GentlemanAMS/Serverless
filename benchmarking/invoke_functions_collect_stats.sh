#!/bin/bash

run_analysis() {

    local FOLDER=$1
    local RPS=$2
    local VSWARM_FOLDER=$HOME/vSwarm/tools/invoker

    mkdir -p $FOLDER

    cp $VSWARM_FOLDER/cleandatfiles.sh $FOLDER/cleanfiles.sh
    chmod +x $FOLDER/cleanfiles.sh

    RESULTS_FILE="$FOLDER/invoke_functions.dat"
    PERF_FILE="$FOLDER/perf.dat"
    MPSTAT_FILE="$FOLDER/mpstat.dat"
    OUTPUT_JSON_FILE="$FOLDER/output.json"
    OUTPUT_PNG1_FILE="$FOLDER/png1.png"

    # Define variables
    PORT=80
    DEBUG_FLAG="false"
    TIME=900
    STATISTICS_INTERVAL=30000

    # Run the command
    cd $VSWARM_FOLDER
    python3 collect_endpoints.py
    make invoker
    sudo ./invoker -port $PORT -time $TIME -rps $RPS -dbg=$DEBUG_FLAG -perf=$PERF_FILE -mpstat=$MPSTAT_FILE -statinterval=$STATISTICS_INTERVAL > $RESULTS_FILE
    python3 ./statanalysis.py $PERF_FILE $MPSTAT_FILE $RESULTS_FILE $OUTPUT_JSON_FILE $TIME
    python3 ./plotstatanalysis.py $OUTPUT_JSON_FILE $OUTPUT_PNG1_FILE
    $VSWARM_FOLDER/cleandatfiles.sh

}

VSWARM_FOLDER=$HOME/vSwarm/tools/invoker

RPS=5
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=50
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=100
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=150
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=200
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=250
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=350
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=500
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=750
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS

RPS=1000
FOLDER=$VSWARM_FOLDER/expt1/rps$RPS
run_analysis $FOLDER $RPS
