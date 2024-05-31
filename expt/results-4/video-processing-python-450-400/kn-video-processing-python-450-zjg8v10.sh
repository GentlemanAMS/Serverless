#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-processing/video-processing-database.yaml
kubectl apply -f video-processing-python-450-400/kn-video-processing-python-450-zjg8v10.yaml
