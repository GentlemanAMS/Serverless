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



import argparse
parser = argparse.ArgumentParser(description="Perf analysis.")
parser.add_argument("-iIP","--invokerIP",required=True)
parser.add_argument("-iPORT","--invokerPORT",required=True)
parser.add_argument("-iHOST","--invokerHOSTNAME",required=False, default="Lakshman")
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
    "config-aes-nodejs-700000-707000-200.yaml",
    "config-fibonacci-python-200000-202000-200.yaml",
    "config-image-rotate-go-3-200.yaml",
    "config-image-rotate-go-6-200.yaml",
    "config-image-rotate-python-11-200.yaml",
    "config-image-rotate-python-17-200.yaml",
    "config-rnn-serving-python-1000-1010-200.yaml",
    "config-video-processing-python-1500-200.yaml",
    "config-video-processing-python-450-200.yaml",
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
server_address = (args.invokerIP, int(args.invokerPORT))
sock.bind(server_address)
sock.listen()
connection, client_address = sock.accept()


def wait_for_start_command(connection):
    try:        
        while True:
            data = connection.recv(1024)
            if data:
                received_string = data.decode()
                if "START INVOKER. CONFIG:" in received_string:
                    parts = received_string.split('CONFIG: ')
                    config_filename = parts[1].strip()
                    log.info(f"Invoker received START INVOKER COMMAND. config file: {config_filename}")
                    return config_filename
                
    except Exception as e:
        log.critical(f"Invoker did not receive START INVOKER COMMAND. Error: {e}")
        return None

def invoke_load(invoker_loc, expt_dur, warmup_dur, load_file, log_file):
    command = f"{invoker_loc}/invoker -duration={expt_dur} -dbg=true -min=true -traceFile={load_file} -warmup={warmup_dur} >> {log_file}"
    try:
        log.info(f"invoker command: {command}")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(f"Load is getting invoked. Command started asynchronously. PID: {process.pid}")
        
    except Exception as e:
        log.critical(f"An error occurred while starting the invocation: {e}")


def run_invoker(invoker_loc, endpoint_file_location, rps, expt_dur, lat_file, dur_file, log_file):
    command = f"{invoker_loc}/invoker -time={expt_dur} -profile=true -durf={dur_file} -latf={lat_file} -endpointsFile={endpoint_file_location} -rps={rps} >> {log_file}"
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(f"Invoker is invoking the function of interest. Command started asynchronously. PID: {process.pid}")
        
    except Exception as e:
        log.critical(f"An error occurred while invoking the function of interest: {e}")


def send_start_invocation_command_response(connection, config_filename, success):

    try:
        if success: command = f"START INVOKER. SUCCESS {config_filename}"
        else: command = f"START INVOKER. FAILED {config_filename}"
        message = command.encode()
        connection.sendall(message)
        log.info(f"'{command}' sent to master")
        return 0

    except Exception as e:
        log.critical(f"An error occurred while sending command '{command}' to master. Error: {e}")
        return -1





while True:

    filename=wait_for_start_command(connection=connection)

    try:
        with open(filename, 'r') as file:
            config_data = yaml.safe_load(file)
    except Exception as exc:
        log.critical(f"Error loading YAML file: {exc}. WRONG: Sending reply although invocation does not happen")
        send_start_invocation_command_response(connection=connection, config_filename=filename, success=False)
        continue

    if not os.path.exists(config_data['output-files-path']):
        os.makedirs(config_data['output-files-path'])
    if not os.path.exists(config_data['log-files-path']):
        os.makedirs(config_data['log-files-path'])
    if(config_data['invoke-load']['run']):
        invoke_load(
            invoker_loc=config_data['invoke-load']['binary_path'], 
            expt_dur=config_data['invoke-load']['expt_dur'], 
            warmup_dur=config_data['invoke-load']['warmup_dur'], 
            load_file=config_data['load-generator']['load_json'],
            log_file=f"{config_data['log-files-path']}/{config_data['invoke-load']['log_file']}"
        )

    if(config_data['invoke-service']['run']): 
        run_invoker(
            invoker_loc=config_data['invoke-service']['binary_path'], 
            endpoint_file_location=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}", 
            rps=config_data['invoke-service']['rps'], 
            expt_dur=config_data['invoke-service']['expt_dur']*60,
            lat_file=f"{config_data['log-files-path']}/{config_data['invoke-service']['lat_file']}", 
            dur_file=f"{config_data['output-files-path']}/{config_data['invoke-service']['dur_file']}", 
            log_file=f"{config_data['log-files-path']}/{config_data['invoke-service']['log_file']}"
        )

    send_start_invocation_command_response(connection=connection, config_filename=filename, success=True)

connection.close()

# time.sleep(20)


