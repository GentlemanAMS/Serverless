import os
import re
import numpy as np

# function_name = "aes-go-1000000-1010000"

def converge_results(function_name):

    folders = [f"{function_name}-10", f"{function_name}-200", f"{function_name}-300", f"{function_name}-400"]

    keywords = {
        "cpu-cycles": r"(\d[\d,]*)\s+cpu-cycles",
        "instructions": r"(\d[\d,]*)\s+instructions",
        "context-switches": r"(\d[\d,]*)\s+context-switches"
    }


    def extract_value(pattern, text):
        match = re.search(pattern, text)
        if match:
            return int(match.group(1).replace(',', ''))
        return None

    def search_in_file(file_path):
        results = {}
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                for key, pattern in keywords.items():
                    results[key] = extract_value(pattern, content)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        return results

    # all_results = []
    # for folder in folders:
    #     file_path = os.path.join(folder, 'perf.txt')
    #     search_results = search_in_file(file_path)
    #     if all(val is not None for val in search_results.values()):
    #         cpu_cycles = search_results["cpu-cycles"]
    #         instructions = search_results["instructions"]
    #         context_switches = search_results["context-switches"]
    #         cpi = cpu_cycles / instructions
    #         ipc = instructions / cpu_cycles
    #         all_results.append((folder, cpu_cycles, instructions, context_switches, cpi, ipc))

    # # Print results in a tabular format
    # print(f"{'Folder':<40} {'CPU Cycles':<15} {'Instructions':<15} {'Context Switches':<18} {'CPI':<15} {'IPC':<15}")
    # for result in all_results:
    #     folder, cpu_cycles, instructions, context_switches, cpi, ipc = result
    #     print(f"{folder:<40} {cpu_cycles:<15} {instructions:<15} {context_switches:<18} {cpi:<15.10f} {ipc:<15.10f}")

    def search_in_mpstat_file(file_path):
        results = {}
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    if line.startswith("Average:"):
                        parts = line.split()
                        results['user'] = float(parts[2])
                        results['system'] = float(parts[4])
                        results['idle'] = float(parts[-1])
                        break
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        return results

    def search_in_invoker_log(file_path):
        results = {}
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    if 'level=info msg="Issued / completed requests' in line:
                        pattern = r'Issued / completed requests: (\d+), (\d+)'
                        match = re.search(pattern, line)
                        if match:
                            issued = int(match.group(1))
                            completed = int(match.group(2)) - 1
                            results['issued_requests'] = issued
                            results['completed_requests'] = completed
                        break
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        return results

    def calculate_dur_stats(file_path):
        try:
            with open(file_path, 'r') as file:
                data = [int(line.strip()) for line in file.readlines()]
                if data:
                    mean = np.mean(data)
                    stddev = np.std(data)
                    minimum = np.min(data)
                    maximum = np.max(data)
                    p25 = np.percentile(data, 25)
                    p50 = np.percentile(data, 50)
                    p75 = np.percentile(data, 75)
                    p95 = np.percentile(data, 95)
                    return {
                        "dur-mean": mean,
                        "dur-stddev": stddev,
                        "dur-min": minimum,
                        "dur-max": maximum,
                        "dur-p25": p25,
                        "dur-p50": p50,
                        "dur-p75": p75,
                        "dur-p95": p95
                    }
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        return None


    def calculate_lat_stats(file_path):
        try:
            with open(file_path, 'r') as file:
                data = [int(line.strip()) for line in file.readlines()]
                if data:
                    mean = np.mean(data)
                    stddev = np.std(data)
                    minimum = np.min(data)
                    maximum = np.max(data)
                    p25 = np.percentile(data, 25)
                    p50 = np.percentile(data, 50)
                    p75 = np.percentile(data, 75)
                    p95 = np.percentile(data, 95)
                    return {
                        "lat-mean": mean,
                        "lat-stddev": stddev,
                        "lat-min": minimum,
                        "lat-max": maximum,
                        "lat-p25": p25,
                        "lat-p50": p50,
                        "lat-p75": p75,
                        "lat-p95": p95
                    }
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        return None


    all_results = {}
    for folder in folders:

        file_path = os.path.join(folder, 'perf.txt')
        search_results = search_in_file(file_path)
        if all(val is not None for val in search_results.values()) and search_results != {}:
            cpu_cycles = search_results["cpu-cycles"]
            instructions = search_results["instructions"]
            context_switches = search_results["context-switches"]
            cpi = cpu_cycles / instructions
            ipc = instructions / cpu_cycles
        else:
            cpu_cycles = instructions = context_switches = cpi = ipc = None

        mpstat_path = os.path.join(folder, 'mpstat.txt')
        mpstat_results = search_in_mpstat_file(mpstat_path)
        if all(key in mpstat_results for key in ['user', 'system', 'idle']):
            user = mpstat_results['user']
            system = mpstat_results['system']
            idle = mpstat_results['idle']
        else:
            user = system = idle = None

        invoker_log_path = os.path.join(folder, 'invoker-service.log')
        invoker_results = search_in_invoker_log(invoker_log_path)
        if all(key in invoker_results for key in ['issued_requests', 'completed_requests']):
            issued_requests = invoker_results['issued_requests']
            completed_requests = invoker_results['completed_requests']
        else:
            issued_requests = completed_requests = None

        dur_path = os.path.join(folder, 'dur.txt')
        dur_stats = calculate_dur_stats(dur_path)

        lat_path = os.path.join(folder, 'lat.txt')
        lat_stats = calculate_lat_stats(lat_path)

        all_results[folder] = {
            "cpu-cycles": cpu_cycles,
            "instructions": instructions,
            "context-switches": context_switches,
            "cpi": cpi,
            "ipc": ipc,
            "user-util": user,
            "system-util": system,
            "idle-util": idle,
            "issued_req": issued_requests,
            "completed_req": completed_requests
        }
        if dur_stats is not None:
            all_results[folder].update(dur_stats)
        if lat_stats is not None:
            all_results[folder].update(lat_stats)


    # Print results in a transposed tabular format
    metrics = [
        "cpu-cycles", "instructions", "context-switches", "cpi", "ipc",
        "user-util", "system-util", "idle-util", "issued_req", "completed_req",
        "dur-mean", "dur-stddev", "dur-min", "dur-max", "dur-p25", "dur-p50", "dur-p75", "dur-p95",
        "lat-mean", "lat-stddev", "lat-min", "lat-max", "lat-p25", "lat-p50", "lat-p75", "lat-p95"
    ]
    header = f"{'Metric':<20}" + "".join([f"{folder:<15}" for folder in ["10", "200", "300", "400"]])
    print(f"{function_name}\n")
    print(header)

    for metric in metrics:
        row = f"{metric:<20}"
        for folder in folders:
            if folder in all_results:
                value = all_results[folder][metric]
                if value is None:
                    row += f"{'N/A':<15}"
                elif isinstance(value, float):
                    row += f"{value:<15.5f}"
                else:
                    row += f"{value:<15}"
            else:
                row += f"{'N/A':<15}"
        print(row)
    print("\n\n\n")

functions = [
    "aes-nodejs-100000-101000",
    "aes-nodejs-700000-707000",
    "aes-go-1000000-1010000",
    "aes-python-500-505",
    "aes-python-45000-45450",
    "aes-python-200000-202000",
    "fibonacci-go-70000-70700",
    "fibonacci-go-200000-202000",
    "fibonacci-go-450000-454500",
    "fibonacci-python-20000-20200",
    "fibonacci-python-200000-202000",
    "gptj-python",
    "image-rotate-go-3",
    "image-rotate-go-6",
    "image-rotate-go-14",
    "image-rotate-python-7",
    "image-rotate-python-11",
    "image-rotate-python-17",
    "rnn-serving-python-20-20",
    "rnn-serving-python-100-101",
    "rnn-serving-python-1000-1010",
    "video-analytics-standalone-python-10",
    "video-analytics-standalone-python-30",
    "video-analytics-standalone-python-70",
    "video-processing-python-70",
    "video-processing-python-450",
    "video-processing-python-1500"
]

for f in functions:
    converge_results(f)