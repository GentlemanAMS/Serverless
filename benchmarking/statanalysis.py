import re
import sys
from collections import OrderedDict
import json
import matplotlib.pyplot as plt

if len(sys.argv) != 6:
    print("Usage: python script.py <perf.dat> <mpstat.dat> <invoke_functions.dat> <output_file.json> <time_ran>")
    sys.exit(1)

perf_file_path = sys.argv[1]
mpstat_file_path = sys.argv[2]
invoke_functions_data_filepath = sys.argv[3]
output_json_file = sys.argv[4]
time_ran = int(sys.argv[5])

statanalysis = OrderedDict()
statanalysis["Total-Time-Stats-Collected"] = (time_ran * 0.1, time_ran * 0.9)
statanalysis["time"] = OrderedDict()

# Function to parse the input file and create a dictionary
def parse_cpustat_data(perf_file_path, mpstat_file_path):

    file = open(perf_file_path, 'r')
    lines = file.readlines()
    file.close()
    lines = lines[3:]

    for i in range(len(lines)):

        try:
            line = lines[i]
            line = line.split()
            time = float(line[0])
            counts = int(line[1].replace(',',''))
            unit = line[2]

            # This can be done through regex statement
            # match = re.match(r'\s*([\d.]+)\s+([\d,]+)\s+(\S+)\s*', line)
            # if match:
            #     time = float(match.group(1))
            #     counts = int(match.group(2).replace(',', ''))
            #     unit = match.group(3)

            time = float("{:.3f}".format(time))
            if time not in statanalysis["time"].keys():
                statanalysis["time"][time] = {}
            statanalysis["time"][time][unit] = counts
            
        except:
            pass


    file = open(mpstat_file_path, 'r')
    lines = file.readlines()
    file.close()
    lines = lines[3:]

    for i in range(len(lines)):

        try:
            line = lines[i]
            line = line.split()
            idle_percentage = float(line[-1])
            cpu_utilization = 100 - idle_percentage
            cpu_utilization = float("{:.2f}".format(cpu_utilization))

            # match = re.match(r'\d{2}:\d{2}:\d{2} AM\s+all\s+(.*)', line)
            # if match:
            #     idle_percentage = float(match.group(1))
            #     idle_percentages.append(idle_percentage)

            statanalysis["time"][list((statanalysis["time"]).keys())[i]]["CPU-utilization"] = cpu_utilization

        except:
            pass

    # for time in statanalysis["time"].keys():
    #     print(f"Time: {time}")
    #     for unit in statanalysis["time"][time].keys():
    #         print(f"\t{unit}: {statanalysis['time'][time][unit]}")

def parse_invoke_functions_data(invoke_functions_data_filepath):

    file = open(invoke_functions_data_filepath, 'r')
    lines = file.readlines()
    file.close()

    def extract_numbers(log_message):
        numbers = re.findall(r"\d+\.\d+|\d+", log_message)
        return [float(num) if '.' in num else int(num) for num in numbers]

    for line in lines:
        pattern = re.compile(r'completed requests')
        if bool(pattern.search(line)):
            Issued_requests = extract_numbers(line)[-2]
            Completed_requests = extract_numbers(line)[-1]
        pattern = re.compile(r'target RPS')
        if bool(pattern.search(line)):
            Real_RPS = extract_numbers(line)[-2]
            Target_RPS = extract_numbers(line)[-1]

    statanalysis["Issued-requests"] = Issued_requests
    statanalysis["Completed-requests"] = Completed_requests
    statanalysis["Real-RPS"] = Real_RPS
    statanalysis["Target-RPS"] = Target_RPS

    # print(f"Issued requests: {Issued_requests}")
    # print(f"Completed requests: {Completed_requests}")
    # print(f"Real RPS: {Real_RPS}")
    # print(f"Target RPS: {Target_RPS}")


def average_stats():

    average_cpu_utilization = 0
    total_LLC_loads = 0
    total_LLC_load_misses = 0
    total_LLC_stores = 0
    total_LLC_stores_misses = 0

    for time in statanalysis["time"].keys():
        total_LLC_loads += statanalysis["time"][time]["LLC-loads"]
        total_LLC_load_misses += statanalysis["time"][time]["LLC-load-misses"]
        total_LLC_stores += statanalysis["time"][time]["LLC-stores"]
        total_LLC_stores_misses += statanalysis["time"][time]["LLC-store-misses"]
        average_cpu_utilization += statanalysis["time"][time]["CPU-utilization"]

    average_cpu_utilization = average_cpu_utilization / len(statanalysis["time"])
    average_cpu_utilization = float("{:.2f}".format(average_cpu_utilization))

    statanalysis["Average-CPU-Utilization"] = average_cpu_utilization
    statanalysis["Total-LLC-loads"] = total_LLC_loads
    statanalysis["Total-LLC-loads-misses"] = total_LLC_load_misses
    statanalysis["Total-LLC-stores"] = total_LLC_stores
    statanalysis["Total-LLC-stores-misses"] = total_LLC_stores_misses


def get_endpoints():
    # Read JSON data from file
    with open('endpoints.json', 'r') as json_file:
        json_data = json.load(json_file)

    # Extracting endpoints
    endpoints = [entry["hostname"] for entry in json_data]
    statanalysis["endpoints"] = endpoints


parse_cpustat_data(perf_file_path, mpstat_file_path)
parse_invoke_functions_data(invoke_functions_data_filepath)
average_stats()
get_endpoints()

with open(output_json_file, 'w') as json_file:
    json.dump(statanalysis, json_file, indent=4)

