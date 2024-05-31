#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-processing/video-processing-database.yaml
kubectl apply -f video-processing-python-1500-400/kn-video-processing-python-1500-n6wi3mq.yaml
