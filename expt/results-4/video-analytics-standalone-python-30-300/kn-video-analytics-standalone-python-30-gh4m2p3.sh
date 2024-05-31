#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-analytics-standalone/video-analytics-standalone-database.yaml
kubectl apply -f video-analytics-standalone-python-30-300/kn-video-analytics-standalone-python-30-gh4m2p3.yaml
