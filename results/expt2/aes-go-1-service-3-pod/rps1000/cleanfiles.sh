#!/bin/bash

VSWARM_FOLDER=$HOME/vSwarm/tools/invoker
FOLDER=.

sudo rm $FOLDER/perf.dat
sudo rm $FOLDER/mpstat.dat
sudo rm $FOLDER/invoke_functions.dat
sudo rm $FOLDER/output.json
sudo rm $FOLDER/png1.png

sudo rm $VSWARM_FOLDER/rps*
