#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-analytics-standalone/video-analytics-standalone-database.yaml
kubectl apply -f video-analytics-standalone-python-10-10/kn-video-analytics-standalone-python-10-la80zoj.yaml
