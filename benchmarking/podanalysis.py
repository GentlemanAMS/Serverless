import subprocess
import sys
import json
import os
import psutil 
import time
from collections import OrderedDict

home_directory = os.path.expanduser("~")

if len(sys.argv) != 3:
    print("Usage: python script.py <output_file.json> <timestamp>")
    sys.exit(1)

output_json_file = sys.argv[1]
timestamp = sys.argv[2]

try:
    with open(output_json_file, "r") as file:
        podanalysis = json.load(file, object_pairs_hook=OrderedDict)
except FileNotFoundError:
    podanalysis = OrderedDict()
    podanalysis["services"] = OrderedDict()
    podanalysis["pods"] = OrderedDict()


def get_service_list():
    try:
        command = f"kn service list"
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        services = [line.split()[0] for line in result.stdout.strip().split('\n')[1:]]
        return services
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)


def get_pod_list(services_deployed):

    pods = {}

    def run_kubectl_command_to_get(): 
        try:
            result = subprocess.run(["kubectl","get","pods"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                result = result.stdout
                return result
            else:
                print(f"Error: {result.stderr}")
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            sys.exit(1)

    command_result = run_kubectl_command_to_get()
    command_result = command_result.split('\n')
    command_result = command_result[1:]     # Removing header
    command_result = command_result[:-2]    # Removing last endline - empty line

    for line in command_result:

        line = line.split()
        pod_name = line[0]
        pod_status = line[2]

        pod_service = []
        for service in services_deployed:
            if service in pod_name:
                pod_service.append(service)
        try:
            command = f"kubectl get pod {pod_name} -o=json | jq '.metadata.labels[\"serving.knative.dev/service\"]'"
            result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0: pod_service = result.stdout.replace('"','').replace(' ','').replace('\n','') 
            else: print("XXX")
        except subprocess.CalledProcessError as e: print(e)

        pods[pod_name] = {}
        pods[pod_name]['name'] = pod_name 
        pods[pod_name]['status'] = pod_status 
        pods[pod_name]['service'] = pod_service
    return pods

def parse_pods_details(pods, services_deployed):

    pods_by_services = {}
    for service in services_deployed:
        pods_by_services[service] = {}
        pods_by_services[service]['name'] = []
        pods_by_services[service]['status'] = {}

    # Removing pods that are not services. Ex: online-database and stuffs like that
    pod_names_to_be_deleted = []
    for pod_name in pods.keys():
        service = pods[pod_name]['service']
        if service not in services_deployed:
            pod_names_to_be_deleted.append(pod_name)
    for pod_name in pod_names_to_be_deleted:
        pods.pop(pod_name)

    for pod_name in pods.keys():
        service = pods[pod_name]['service']
        status = pods[pod_name]['status']
        pods_by_services[service]['name'].append(pods[pod_name]['name'])
        if status not in pods_by_services[service]['status'].keys():
            pods_by_services[service]['status'][status] = 0
        pods_by_services[service]['status'][status] += 1
    return pods_by_services


services_deployed = get_service_list()
pods = get_pod_list(services_deployed)
pods_by_services = parse_pods_details(pods, services_deployed)

podanalysis["services"][timestamp] = pods_by_services
podanalysis["pods"][timestamp] = pods
with open(output_json_file, "w") as file:
    json.dump(podanalysis, file, indent=2)