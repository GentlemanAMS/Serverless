#!/bin/bash

VSWARM=$HOME/vSwarm/tools/invoker
BENCHMARK=$HOME/benchmarking

cp $BENCHMARK/client.go $VSWARM/
cp $BENCHMARK/collect_endpoints.py $VSWARM/
cp $BENCHMARK/cleandatfiles.sh $VSWARM/
cp $BENCHMARK/invoke_functions.sh $VSWARM/
cp $BENCHMARK/invoke_functions_collect_stats.sh $VSWARM/
cp $BENCHMARK/plotstatanalysis.py $VSWARM/
cp $BENCHMARK/statanalysis.py $VSWARM/
