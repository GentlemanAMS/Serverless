# Python code to plot the Average rps from invoker logs:
# Looks for the string ""Average Real RPS: <rps>" in the invoker logs and plots the rps values.

import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import argparse

def parse_load_log(file):
    with open(file, 'r') as f:
        lines = f.readlines()
    rps = []
    for line in lines:
        if "Average Real RPS:" in line:
            rps.append(float(line.split()[-2]))
    return rps

argparser = argparse.ArgumentParser()
argparser.add_argument('-d', '--directory', help='Absolute path to directory containing invoker load log files', required=True)
argparser.add_argument('-o', '--output', help='Output file', required=True)
args = argparser.parse_args()

files = glob.glob(os.path.join(args.directory, '*/invoker-load.log'))
data = {}
x_ticks_labels = []
for file in files:
    label = file.split('/')[-2]
    # Get only the last token from the hyphen separated string
    label = label.split('-')[-1]
    label = int(label)
    data[label] = parse_load_log(file)
    x_ticks_labels.append(label)

x_ticks_labels = sorted(x_ticks_labels)

rps = []

for label in x_ticks_labels:
    rps.append(data[label])

# Plot
fig, ax = plt.subplots()
ax.plot(x_ticks_labels, rps, marker='o')
ax.set_xlabel('Trace')
ax.set_ylabel('RPS')
ax.set_title('RPS vs Trace')
plt.savefig(args.output)