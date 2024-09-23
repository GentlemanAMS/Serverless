# Python code to plot perf data from multiple folders
# Usage: python3 perf_plot.py -d <directory> -o <output_file>  

import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import argparse
# Sample perf file
# Performance counter stats for 'system wide':
#
#          2,189.68 msec cpu-clock                 #   36.766 CPUs utilized          
#             1,115      context-switches          #    0.509 K/sec                  
#                13      cpu-migrations            #    0.006 K/sec                  
#             3,542      page-faults               #    0.002 M/sec                  
#       179,363,343      cycles                    #    0.082 GHz                    
#       111,098,066      instructions              #    0.62  insn per cycle         
#        22,476,718      branches                  #   10.265 M/sec                  
#           943,954      branch-misses             #    4.20% of all branches        
#
#       0.059557330 seconds time elapsed

def parse_perf_file(file):
    data = {}
    with open(file, 'r') as f:
        for line in f:
            line = line.strip().split()
            if len(line) < 3:
                continue
            if line[2] == 'cpu-clock':
                data['cpu-clock'] = float(line[0].replace(',', ''))
            elif line[1] == 'context-switches':
                data['context-switches'] = float(line[0].replace(',', ''))
            elif line[1] == 'cpu-migrations':
                data['cpu-migrations'] = float(line[0].replace(',', ''))
            elif line[1] == 'page-faults':
                data['page-faults'] = float(line[0].replace(',', ''))
            elif line[1] == 'cycles':
                data['cycles'] = float(line[0].replace(',', ''))
            elif line[1] == 'instructions':
                data['instructions'] = float(line[0].replace(',', ''))
            elif line[1] == 'branches':
                data['branches'] = float(line[0].replace(',', ''))
            elif line[1] == 'branch-misses':
                data['branch-misses'] = float(line[0].replace(',', ''))

    return data

argparser = argparse.ArgumentParser()
argparser.add_argument('-d', '--directory', help='Absolute path to directory containing mpstat files', required=True)
argparser.add_argument('-o', '--output', help='Output file prefix', required=True)
args = argparser.parse_args()

files = glob.glob(os.path.join(args.directory, '*/perf.txt'))
data = {}
x_ticks_labels = []
for file in files:
    label = file.split('/')[-2]
    # Get only the last token from the hyphen separated string
    label = label.split('-')[-1]
    label = int(label)
    data[label] = parse_perf_file(file)
    x_ticks_labels.append(label)


# Sort data by file name
x_ticks_labels = sorted(x_ticks_labels)
    
# Three separate plots, one for IPC, one for branch misses per kilo instruction, one for context switches

ipc = []
branch_misses = []
context_switches = []

# Gather user times
for label in x_ticks_labels:
    ipc.append(data[label]['instructions'] / data[label]['cycles'])
    branch_misses.append(data[label]['branch-misses'] / (data[label]['instructions'] / 1000))
    context_switches.append(data[label]['context-switches'])

op_ipc = args.output + "_ipc.png"
op_branch_misses = args.output + "_branch_misses.png"
op_context_switches = args.output + "_context_switches.png"

# Plot IPC
plt.figure()
plt.plot(x_ticks_labels, ipc, label='IPC', color='blue')
plt.xlabel('Number of Functions')
plt.ylabel('Instructions per Cycle')
plt.title('Instructions per Cycle (IPC)')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(op_ipc)

# Plot Branch Misses

plt.figure()
plt.plot(x_ticks_labels, branch_misses, label='Branch Misses', color='orange')
plt.xlabel('Number of Functions')
plt.ylabel('Branch Misses per Kilo Instruction')
plt.title('Branch Misses per Kilo Instruction')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(op_branch_misses)

# Plot Context Switches

plt.figure()
plt.plot(x_ticks_labels, context_switches, label='Context Switches', color='green')
plt.xlabel('Number of Functions')
plt.ylabel('Context Switches')
plt.title('Context Switches')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(op_context_switches)
