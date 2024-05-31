#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-processing/video-processing-database.yaml
kubectl apply -f video-processing-python-450-10/kn-video-processing-python-450-rh5sh3x.yaml
