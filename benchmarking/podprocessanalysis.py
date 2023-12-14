import subprocess
import sys
import json
import os
import psutil 

home_directory = os.path.expanduser("~")

# def read_endpoints_json():
#     file_path = home_directory + "/vSwarm/tools/invoker/endpoints.json"
#     try:
#         with open(file_path, 'r') as file:
#             data = json.load(file)
#             hostnames = [entry.get("hostname", "") for entry in data]
#             return hostnames
#     except json.JSONDecodeError as e:
#         print(f"Error decoding JSON: {e}")
#         return None
#     except FileNotFoundError:
#         print(f"Error: File not found at {file_path}")
#         return None 


# def get_service_list(endpoints):
#     result = [hostname.split('.')[0] for hostname in endpoints]
#     return result


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
        pod_age = line[4]
        pod_service = None
        for service in services_deployed:
            if service in pod_name:
                pod_service = service
                break
        pods[pod_name] = {}
        pods[pod_name]['name'] = pod_name 
        pods[pod_name]['status'] = pod_status 
        pods[pod_name]['age'] = pod_age
        pods[pod_name]['service'] = pod_service
        pods[pod_name]['processes'] = []  
        pods[pod_name]['container-args'] = []   

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
        if service not in pods_by_services.keys():
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


def get_process_list():
    processes = []
    all_processes = psutil.process_iter()
    for process in all_processes:
        procinfo = process.as_dict(attrs=['pid', 'name', 'cmdline', 'username'])
        process_details = {}
        process_details['pid'] = procinfo['pid']
        process_details['name'] = procinfo['name']
        process_details['cmdline'] = procinfo['cmdline']
        process_details['username'] = procinfo['username']
        processes.append(process_details)
    return processes


def get_process_of_pod_using_nsenter(processes, pods):

    for procinfo in processes:
        pid = procinfo['pid']
        name = procinfo['name']
        cmdline = procinfo['cmdline']
        username = procinfo['username']
        try:
            command = f"sudo nsenter -t {pid} -u hostname"
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)            
            if result.returncode == 0:
                namespace = result.stdout.strip()
                if namespace in pods.keys():
                    pods[namespace]['processes'].append([pid, name, cmdline, username]) 
            else:
                continue

        except subprocess.CalledProcessError as e:
            continue


# def container_args_pods(pods):

#     def get_container_arg(pod_name):

#         try:
#             command = f"kubectl get pod {pod_name} -o=json"
#             result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#             pod_info = json.loads(result.stdout)
#             containers = pod_info['spec']['containers']
#         except subprocess.CalledProcessError as e:
#             return

#         for container in containers:
#             if 'args' in container:
#                 container_args = container['args'] 
#                 temp = ' '.join(container_args)
#                 if (('--addr=' in temp) and ('--function-endpoint-url=' in temp) and ('--function-endpoint-port=' in temp) and ('--function-name=' in temp)):
#                     pods[pod_name]['container-args'].append(temp)

#     for pod_name in pods.keys():
#         get_container_arg(pod_name)


# def get_process_using_pid(pods):

#     def get_process(pod_name):

#         try:

#             containers_args = pods[pod_name]['container-args']

#             for args in containers_args: 

#                 command = f'pgrep -af -- "{args}"'
#                 result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#                 processes = result.stdout.split('\n')
#                 processes = [process for process in processes if process != '']

#                 for process in processes:

#                     process = process.split()
#                     pid = process[0]
#                     command = f"sudo nsenter -t {pid} -u hostname"
#                     result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
#                     if result.returncode == 0:
#                         namespace = result.stdout.strip()
#                         if namespace in pods.keys():
#                             pods[namespace]['processes'].append(pid)

#         except subprocess.CalledProcessError as e:
#             return

#     for pod_name in pods.keys():
#         get_process(pod_name)


# endpoints = read_endpoints_json()
# services_deployed = get_service_list(endpoints)
services_deployed = get_service_list()
pods = get_pod_list(services_deployed)
pods_by_services = parse_pods_details(pods, services_deployed)
process_list = get_process_list()
get_process_of_pod_using_nsenter(process_list, pods)
# container_args_pods(pods)
# get_process_using_pid(pods)
print(json.dumps(pods, indent=3))
