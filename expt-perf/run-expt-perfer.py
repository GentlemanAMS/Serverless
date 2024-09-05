import subprocess
import yaml
import string
import secrets
import stat
import os
import time
import json
import sys
from log_config import *
import socket
import re


import argparse
parser = argparse.ArgumentParser(description="Perf analysis.")
parser.add_argument("-pIP","--perfIP",required=True)
parser.add_argument("-pPORT","--perfPORT",required=True)
parser.add_argument("-pHOST","--perfHOSTNAME",required=False, default="Lakshman")
args = parser.parse_args()

yaml_files = [
    "config-aes-nodejs-700000-707000-10.yaml",
    "config-fibonacci-python-200000-202000-10.yaml",
    "config-image-rotate-go-3-10.yaml",
    "config-image-rotate-go-6-10.yaml",
    "config-image-rotate-python-11-10.yaml",
    "config-image-rotate-python-17-10.yaml",
    "config-rnn-serving-python-1000-1010-10.yaml",
    "config-video-processing-python-1500-10.yaml",
    "config-video-processing-python-450-10.yaml",
    "config-aes-nodejs-700000-707000-100.yaml",
    "config-fibonacci-python-200000-202000-100.yaml",
    "config-image-rotate-go-3-100.yaml",
    "config-image-rotate-go-6-100.yaml",
    "config-image-rotate-python-11-100.yaml",
    "config-image-rotate-python-17-100.yaml",
    "config-rnn-serving-python-1000-1010-100.yaml",
    "config-video-processing-python-1500-100.yaml",
    "config-video-processing-python-450-100.yaml",
    "config-aes-nodejs-700000-707000-200.yaml",
    "config-fibonacci-python-200000-202000-200.yaml",
    "config-image-rotate-go-3-200.yaml",
    "config-image-rotate-go-6-200.yaml",
    "config-image-rotate-python-11-200.yaml",
    "config-image-rotate-python-17-200.yaml",
    "config-rnn-serving-python-1000-1010-200.yaml",
    "config-video-processing-python-1500-200.yaml",
    "config-video-processing-python-450-200.yaml",
    "config-aes-nodejs-700000-707000-300.yaml",
    "config-fibonacci-python-200000-202000-300.yaml",
    "config-image-rotate-go-3-300.yaml",
    "config-image-rotate-go-6-300.yaml",
    "config-image-rotate-python-11-300.yaml",
    "config-image-rotate-python-17-300.yaml",
    "config-rnn-serving-python-1000-1010-300.yaml",
    "config-video-processing-python-1500-300.yaml",
    "config-video-processing-python-450-300.yaml",
    "config-aes-nodejs-700000-707000-450.yaml",
    "config-fibonacci-python-200000-202000-450.yaml",
    "config-image-rotate-go-3-450.yaml",
    "config-image-rotate-go-6-450.yaml",
    "config-image-rotate-python-11-450.yaml",
    "config-image-rotate-python-17-450.yaml",
    "config-rnn-serving-python-1000-1010-450.yaml",
    "config-video-processing-python-1500-450.yaml",
    "config-video-processing-python-450-450.yaml",
]

for filepath in yaml_files:
    with open(filepath, 'r') as file:
        try:
            config_data = yaml.safe_load(file)
        except Exception as e:
            log.critical(f"Error loading YAML file: {e}")
            continue

    if not os.path.exists(config_data['output-files-path']):
        os.makedirs(config_data['output-files-path'])
    if not os.path.exists(config_data['log-files-path']):
        os.makedirs(config_data['log-files-path'])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (args.perfIP, int(args.perfPORT))
sock.bind(server_address)
sock.listen()
connection, client_address = sock.accept()



def wait_for_start_command(connection):

    try:
        while True:
            data = connection.recv(1024)
            if data:
                received_string = data.decode()
                match = re.search(r'CONFIG:\s*(\S+)\s+POD:\s*(\S+)', received_string)
                if match:
                    config_filename = match.group(1)
                    pod_name = match.group(2)
                    log.info(f"Perfer received START PERFER COMMAND. config file: {config_filename}, pod name: {pod_name}")
                    return config_filename, pod_name
    
    except Exception as e:
        log.critical(f"Perfer did not receive START PERFER COMMAND. Error: {e}")
        return None, None



def get_pid(pod_name, grep_string):

    get_process_list = f"ps aux | grep '{grep_string}'"
    try:
        result = subprocess.run(
            get_process_list,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = result.stdout.decode("utf-8").strip().split("\n")
    except subprocess.CalledProcessError as e:
        log.error(
            f"Can't get the list of processes. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}"
        )
        return None
    except Exception as e:
        log.warning(f"Can't get the list of processes. Error: {e}")
        return None

    for line in result:
        try:
            line = line.split()
            pid = line[1]
            command = f"sudo nsenter -t {pid} -u hostname"
            nsenter_result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
            if nsenter_result.returncode == 0:
                namespace = nsenter_result.stdout.strip()
                if pod_name in namespace:
                    log.info(f"Found PID of the process: {pid}")
                    return pid
        except Exception as e:
            continue

    log.error(f"PID of the process of pod {pod_name} not found")
    return None        
        

def run_taskset (pid, cpu):

    run_taskset_command = f"sudo taskset -pc {cpu} {pid}"
    try:
        _ = subprocess.run(
            run_taskset_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        log.info(f"Taskset process PID {pid} to CPU {cpu}")
        
    except Exception as e:
        log.error(f"An error occurred while tasksetting: {e}")


def run_mpstat( output_file, interval, count):
    
    run_mpstat_command = f"sudo mpstat {interval} {count} >> {output_file}"
    try:
        process = subprocess.Popen(
            run_mpstat_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        log.info(f"MPStat collection. Command started asynchronously. PID: {process.pid}")

    except Exception as e:
        log.error(f"An error occurred while mpstat collection: {e}")
    



def run_perf(event_list, pid, warmup_dur, expt_dur, interval_print, output_file):

    interval_count = int(expt_dur/interval_print)
    run_perf_command = f"sudo perf stat -e "
    for i in range(len(event_list)):
        run_perf_command += f"{event_list[i]}"
        if i != len(event_list)-1: run_perf_command += f","
    run_perf_command += f" -p {pid}"
    run_perf_command += f" --delay {warmup_dur}"
    run_perf_command += f" -o {output_file}"
    # run_perf_command += f" --timeout {expt_dur}"
    run_perf_command += f" -I {interval_print}"
    run_perf_command += f" --interval-count {interval_count}"
    try:
        # process = subprocess.Popen(
        #     run_perf_command,
        #     shell=True,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        # )

        # log.info(f"Perf stat collection. Command started asynchronously. PID: {process.pid}")
        _ = subprocess.run(
            run_perf_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        log.info(f"Perf stat collection completed")
        
    except Exception as e:
        log.critical(f"An error occurred while perf stat collection: {e}")


def send_start_perfer_command_response(connection, config_filename, success):

    try:
        if success: command = f"PERF COMPLETED. SUCCESS {config_filename}"
        else: command = f"PERF COMPLETED. FAILED {config_filename}"
        message = command.encode()
        connection.sendall(message)
        log.info(f"'{command}' sent to master")        
        return 0

    except Exception as e:
        log.critical(f"An error occurred while sending command '{command}' to master. Error: {e}")
        return -1




while True:

    filename, pod_name = wait_for_start_command(connection=connection)
    try:
        with open(filename, 'r') as file:
            config_data = yaml.safe_load(file)
    except Exception as exc:
        log.critical(f"Error loading YAML file: {exc}. WRONG: Sending reply although perf is failed")
        send_start_perfer_command_response(connection=connection, config_filename=filename, success=False)


    if not os.path.exists(config_data['output-files-path']):
        os.makedirs(config_data['output-files-path'])
    if not os.path.exists(config_data['log-files-path']):
        os.makedirs(config_data['log-files-path'])

    pid = get_pid(pod_name=pod_name, grep_string=config_data['perf']['grep_string'])
    if pid is None:
        log.critical(f"perf failed. PID not found. WRONG: Sending reply although perf is failed")
        send_start_perfer_command_response(connection=connection, config_filename=filename, success=False)
        continue

    if(config_data['taskset-service']['set']):
        run_taskset(cpu=config_data['taskset-service']['cpuid'], pid=pid)

    if(config_data['mpstat']['collect']):
        run_mpstat(
            output_file=f"{config_data['output-files-path']}/{config_data['mpstat']['output_file']}",
            interval=config_data['mpstat']['interval'],
            count=int((config_data['perf']['warmup_dur']+config_data['perf']['expt_dur'])*60/config_data['mpstat']['interval'])
        )

    if(config_data['perf']['collect']):
        run_perf(
            event_list=config_data['perf']['event_list'], 
            pid=pid, 
            warmup_dur=config_data['perf']['warmup_dur']*60*1000, 
            expt_dur=config_data['perf']['expt_dur']*60*1000,
            interval_print=config_data['perf']['interval_print_ms'],
            output_file=f"{config_data['output-files-path']}/{config_data['perf']['output_file']}"
        )

    send_start_perfer_command_response(connection=connection, config_filename=filename, success=True)

connection.close()

