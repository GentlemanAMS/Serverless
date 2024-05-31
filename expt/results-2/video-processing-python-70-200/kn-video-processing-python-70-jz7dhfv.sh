#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-processing/video-processing-database.yaml
kubectl apply -f video-processing-python-70-200/kn-video-processing-python-70-jz7dhfv.yaml
