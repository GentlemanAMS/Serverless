#!/bin/bash
cd /users/ArunAMS/
git clone https://github.com/andikleen/pmu-tools
cd pmu-tools
echo 'export PATH=$PATH:/users/ArunAMS/pmu-tools'  >> ~/.bashrc
sudo sysctl -w kernel.perf_event_paranoid=-1
