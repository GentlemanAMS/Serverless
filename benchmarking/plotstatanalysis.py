import re
import sys
from collections import OrderedDict
import json
import matplotlib.pyplot as plt

if len(sys.argv) != 3:
    print("Usage: python script.py <output.json> <output1.png>")
    sys.exit(1)

jsonfilepath = sys.argv[1]
output1_filepath = sys.argv[2]

json_file = open(jsonfilepath, 'r')
statanalysis = json.load(json_file, object_pairs_hook=OrderedDict)
json_file.close()



def plot_cpu_llcload_llc_store(output1_filepath):

    x_values = list(statanalysis["time"].keys())
    cpu_utilization_list = []
    llc_load_count_list = []
    llc_store_count_list = []
    for time in x_values:
        cpu_utilization_list.append(statanalysis["time"][time]["CPU-utilization"])
        llc_load_count_list.append(statanalysis["time"][time]["LLC-loads"])
        llc_store_count_list.append(statanalysis["time"][time]["LLC-stores"])

    fig, ax1 = plt.subplots()

    ax1.plot(x_values, cpu_utilization_list, label='CPU Utilization', color='blue')
    ax1.set_xlabel('X-axis')
    ax1.set_ylabel('%', color='blue')
    ax1.tick_params('y', colors='blue')

    ax2 = ax1.twinx()

    ax2.plot(x_values, llc_load_count_list, label='LLC Load count', color='green')
    ax2.plot(x_values, llc_store_count_list, label='LLC Store count', color='red')
    ax2.set_ylabel('count', color='green')
    ax2.tick_params('y', colors='green')

    fig.tight_layout()
    fig.legend(loc='upper left')

    plt.savefig(output1_filepath)


plot_cpu_llcload_llc_store(output1_filepath)





        
