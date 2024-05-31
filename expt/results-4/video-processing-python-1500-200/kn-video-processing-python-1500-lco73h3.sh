#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-processing/video-processing-database.yaml
kubectl apply -f video-processing-python-1500-200/kn-video-processing-python-1500-lco73h3.yaml
