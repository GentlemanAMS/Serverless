#!/bin/bash
kubectl apply -f /users/ArunAMS/vSwarm/tools/load-generator/yamls/video-analytics-standalone/video-analytics-standalone-database.yaml
kubectl apply -f video-analytics-standalone-python-70-200/kn-video-analytics-standalone-python-70-yc33q0m.yaml
