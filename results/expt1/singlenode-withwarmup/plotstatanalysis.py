import re
import sys
from collections import OrderedDict
import json
import matplotlib.pyplot as plt

if len(sys.argv) != 3:
    print("Usage: python script.py <output.json> <output1.png>")
    sys.exit(1)

jsonfilepath = sys.argv[1]
output_filepath = sys.argv[2]

json_file = open(jsonfilepath, 'r')
statanalysis = json.load(json_file, object_pairs_hook=OrderedDict)
json_file.close()



def plot_cpu_llcload_llc_store(output_filepath):

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
    ax1.set_xlabel('time')
    ax1.set_ylabel('%', color='blue')
    ax1.tick_params('y', colors='blue')

    ax2 = ax1.twinx()

    ax2.plot(x_values, llc_load_count_list, label='LLC Load count', color='green')
    ax2.plot(x_values, llc_store_count_list, label='LLC Store count', color='red')
    ax2.set_ylabel('count', color='green')
    ax2.tick_params('y', colors='green')

    fig.tight_layout()
    fig.legend(loc='upper left')

    plt.savefig(output_filepath+"/output1.png")


plot_cpu_llcload_llc_store(output_filepath)



def plot_cpuutil(output_filepath):

    x_values = list(statanalysis["time"].keys())
    cpu_utilization_list = []
    sys_utilization_list = []
    usr_utilization_list = []
    for time in x_values:
        cpu_utilization_list.append(statanalysis["time"][time]["CPU-utilization"])
        sys_utilization_list.append(statanalysis["time"][time]["sys-CPU-utilization"])
        usr_utilization_list.append(statanalysis["time"][time]["user-CPU-utilization"])

    fig, ax1 = plt.subplots()

    ax1.plot(x_values, cpu_utilization_list, label='CPU Utilization', color='blue')
    ax1.plot(x_values, sys_utilization_list, label='System Utilization', color='red')
    ax1.plot(x_values, usr_utilization_list, label='User Utilization', color='green')
    ax1.set_xlabel('time')
    ax1.set_ylabel('%', color='blue')
    ax1.tick_params('y', colors='blue')

    fig.tight_layout()
    fig.legend(loc='upper left')

    plt.savefig(output_filepath+"/output2.png")

plot_cpuutil(output_filepath)





def plot_llc(output_filepath):

    x_values = list(statanalysis["time"].keys())
    llc_loads_pki = []
    llc_load_missses_pki = []
    llc_stores_pki = []
    llc_store_misses_pki = []

    for time in x_values:
        llc_loads_pki.append(statanalysis["time"][time]["LLC-loads-PKI"])
        llc_load_missses_pki.append(statanalysis["time"][time]["LLC-load-misses-PKI"])
        llc_stores_pki.append(statanalysis["time"][time]["LLC-stores-PKI"])
        llc_store_misses_pki.append(statanalysis["time"][time]["LLC-store-misses-PKI"])

    fig, ax1 = plt.subplots()

    ax1.plot(x_values, llc_loads_pki, label='LLC-loads-PKI', color='blue')
    ax1.plot(x_values, llc_load_missses_pki, label='LLC-load-misses-PKI', color='red')
    ax1.plot(x_values, llc_stores_pki, label='LLC-stores-PKI', color='green')
    ax1.plot(x_values, llc_store_misses_pki, label='LLC-store-misses-PKI', color='purple')
    ax1.set_xlabel('time')
    ax1.set_ylabel('PKI', color='blue')
    ax1.tick_params('y', colors='blue')

    fig.tight_layout()
    fig.legend(loc='upper left')

    plt.savefig(output_filepath+"/output3.png")

plot_llc(output_filepath)




        
