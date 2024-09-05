# Python code to plot all mpstat data from multiple folders
# Usage: python3 mpstat_plot.py -d <directory> -o <output_file>

import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import argparse

# Sample mpstat file
# Linux 5.4.0-164-generic (node-2.lakshman-214830.rperf-pg0.wisc.cloudlab.us) 	09/04/2024 	_x86_64_	(40 CPU)
#
#10:01:46 AM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
#10:02:46 AM  all   11.36    0.00    9.12    0.01    0.00    0.87    0.00    0.00    0.00   78.64
#10:03:46 AM  all    7.55    0.00    8.49    0.01    0.00    0.79    0.00    0.00    0.00   83.16
#10:04:46 AM  all    7.24    0.00    8.46    0.01    0.00    0.72    0.00    0.00    0.00   83.57
#10:05:46 AM  all    7.07    0.00    8.30    0.01    0.00    0.86    0.00    0.00    0.00   83.77
#Average:     all    8.30    0.00    8.59    0.01    0.00    0.81    0.00    0.00    0.00   82.29

def parse_mpstat_file(file):
    data = []
    with open(file, 'r') as f:
        for line in f:
            if 'Average:' in line:
                line = line.strip().split()
                data.append([float(x) for x in line[2:]])
    return data

argparser = argparse.ArgumentParser()
argparser.add_argument('-d', '--directory', help='Absolute path to directory containing mpstat files', required=True)
argparser.add_argument('-o', '--output', help='Output file', required=True)
args = argparser.parse_args()

files = glob.glob(os.path.join(args.directory, '*/mpstat.txt'))
data = {}
x_ticks_labels = []
for file in files:
    data[file] = parse_mpstat_file(file)
    x_ticks_labels.append(file.split('/')[-2])

# Sort data by file name
x_ticks_labels = sorted(x_ticks_labels)
files = sorted(files)

# NOTE: DICTIONARY IS NOT SORTED
    
# Three separate plots, one for user time, one for sys time, one for idle time without subplot

user = []
syst = []
idle = []

# Gather user times
for file in files:
    user.append([x[0] for x in data[file]])
    syst.append([x[2] for x in data[file]])
    idle.append([x[9] for x in data[file]])

fig, ax = plt.subplots()
ax.plot(x_ticks_labels, user, label='User Time')
ax.plot(x_ticks_labels, syst, label='Sys Time')
ax.plot(x_ticks_labels, idle, label='Idle Time')
ax.set_xlabel('Functions', fontsize=10)
ax.set_ylabel('Time (in %)')
ax.set_title('User, Sys and Idle Times')
ax.legend()
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(args.output)
