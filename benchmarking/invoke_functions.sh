#!/bin/bash

# Define variables
PORT=80
DEBUG_FLAG="-dbg"
TIME=200
RPS=0.1

# Run the command
./invoker -port $PORT $DEBUG_FLAG -time $TIME -rps $RPS

