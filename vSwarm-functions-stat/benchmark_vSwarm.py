import os
import stat
import subprocess

import json
import yaml
import re
import time
import numpy as np
import threading

import logging as log
# import logging
# pip3 install colorlog
from colorlog import ColoredFormatter
from typing import Tuple

# logger = logging.getLogger(__name__)
# formatter = ColoredFormatter(
#     "%(log_color)s%(levelname)s [%(asctime)s] - %(message)s%(reset)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     reset=True,
#     log_colors={
#         'DEBUG': 'cyan',
#         'INFO': 'green',
#         'WARNING': 'yellow',
#         'ERROR': 'red',
#         'CRITICAL': 'red,bg_white',
#     },
#     secondary_log_colors={},
#     style='%'
# )
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)
# log = logger

log.basicConfig(format='%(asctime)s:%(levelname)s - %(message)s', level=log.INFO)

def check_shell_path() -> int:
    # Bash script alone available for the purpose.
    shell_path = os.environ.get('SHELL')
    if 'bash' not in shell_path:
        log.critical(f"{shell_path} is not BASH")
        return -1
    else: return 0



def deploy_service(yaml_filename: str, predeployment_commands: list, postdeployment_commands: list, build_shell_scripts_location: str) -> Tuple[str, int]:
    
    
    # Check whether yaml file exists or not.
    try:
        with open(yaml_filename, 'r'): pass
    except FileNotFoundError:
        log.warning(f"{yaml_filename} YAML File not found")
        return None, -1
    except Exception as e:
        log.warning(f"{yaml_filename} YAML File not found. An error occured: {e}")
        return None, -1
    
    # Check whether folder where shell scripts are to be located exists or not
    if not os.path.exists(build_shell_scripts_location):
        log.info(f"{build_shell_scripts_location} directory does not exist.")
        os.makedirs(build_shell_scripts_location)
        log.info(f"{build_shell_scripts_location} directory created")
    else:
        pass

    # Create a list of commands to be executed
    commands = []
    # Commands to be executed before deployment
    for c in predeployment_commands:
        commands.append(c + '\n')
    # Deployment command
    deployment_command = f"kubectl apply -f {yaml_filename}"
    commands.append(deployment_command + '\n')
    # Commands to be executed after deployment
    for c in postdeployment_commands:
        commands.append(c + '\n')

    # Get shell path
    shell_path = os.environ.get('SHELL')

    # Writing a shell script
    # Creating the shell script file name
    shell_filename = os.path.basename(yaml_filename).replace(".yaml", ".sh")
    shell_filename = f"{build_shell_scripts_location}/{shell_filename}"
    # Writing commands into the shell script
    with open(shell_filename, 'w') as f:
        f.write(f"#!{shell_path}\n")
        for c in commands:
            f.write(c)
    # Setting executable permissions for the shell script
    # Permissions: -rwxr-xr-x
    os.chmod(shell_filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    log.debug(f"{shell_filename} created")

    # Execute the shell script and deploy the function
    execute_shell = f"{shell_path} {shell_filename}"
    try:
        result = subprocess.run(execute_shell, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.debug(f"{shell_filename} executed successfully")
        log.debug(f"Output: ", result.stdout)
    except subprocess.CalledProcessError as e:
        log.warning(f"{shell_filename} execution failed. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
        return None, -1
    except Exception as e:
        log.warning(f"{shell_filename} execution failed. Error: {e}")
        return None, -1
    
    # Get the function name from yaml file
    function_name = None
    try:
        with open(yaml_filename, 'r') as f:
            yaml_data = yaml.safe_load(f)
            function_name = yaml_data["metadata"]["name"]
    except KeyError as e:
        log.warning(f"Function name not found. KeyError:{e}")
        return None, -1
    except FileNotFoundError:
        log.warning(f"{yaml_filename} YAML File not found")
        return None, -1
    except Exception as e:
        log.warning(f"{yaml_filename} YAML File not found. An error occured: {e}")
        return None, -1
    
    # Given the function name, get the service status
    def get_service_status(function_name: str) -> bool:
        try:
            get_service_command = f"kn service list --no-headers"
            result = subprocess.run(get_service_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            services = result.stdout.decode('utf-8').strip().split('\n')
            for s in services:
                try:
                    # TODO: Can this be done better?
                    service_name = s.split()[0]
                    service_status = s.split()[8]
                except IndexError as e:
                    continue
                if function_name in service_name:
                    if service_status == "True": return True
                    else: return False
            return False
        except subprocess.CalledProcessError as e:
            log.warning(f"Service can't be monitored. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            log.warning(f"Service can't be monitored. Error: {e}")
            return False
    
    # Monitor the service, until it is ready
    # Monitoring happens every 5 seconds for 15 minutes. If it shows failure even after that then it returns failure
    monitor_time = 15 * 60
    sleep_time = 5
    status = False
    for _ in range(int(monitor_time / sleep_time)):
        status = get_service_status(function_name)
        if status: break
        else: time.sleep(sleep_time)

    if status:
        log.info(f"{yaml_filename}: {function_name} service deployed")
        return function_name, 0
    else:
        log.warning(f"{yaml_filename}: {function_name} service not deployed")
        return function_name, -1

 


def get_endpoint(function_name: str, endpoint_file_location: str) -> Tuple[str, int]:

    # Get list of all services
    get_service_command = f"kn service list --no-headers"
    try:
        result = subprocess.run(get_service_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        log.warning(f"Endpoints can't be collected. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
        return None, -1
    except Exception as e:
        log.warning(f"Endpoints can't be collected. Error: {e}")
        return None, -1
    
    # Define a regular expression pattern to match URLs
    url_pattern = re.compile(r"http://(\S+)")
    # Find all matches in the output
    urls = re.findall(url_pattern, result)
    # Remove "http://" prefix
    urls = [u.replace("http://","") for u in urls]

    log.debug(f"Following URLs were found: {urls}")

    # There must be only one url since only one function is deployed.
    # If more than one url exists, then consider only the url of the mentioned function 
    endpoint = None
    for u in urls:
        if function_name in u:
            endpoint = u
            break

    if endpoint == None:
        log.warn(f"{function_name} Service Endpoint not found")
        return "", -1
    else:
        log.info(f"{function_name} Service Endpoint found: {endpoint}")
    
    # Convert the list to JSON format
    endpoint = [{'hostname': endpoint}]
    json_output = json.dumps(endpoint, indent=3)

    # Write the JSON output to endpoints.json
    # Check whether folder where endpoints are to be located exists or not
    if not os.path.exists(endpoint_file_location):
        log.info(f"{endpoint_file_location} directory does not exist.")
        os.makedirs(endpoint_file_location)
        log.info(f"{endpoint_file_location} directory created")
    else: pass

    json_file = open(f"{endpoint_file_location}/endpoints.json", 'w')
    json_file.write(json_output)
    json_file.close()

    return endpoint, -1



def delete_all_services() -> int:
    
    # Delete all the services
    try:
        delete_service_command = f"kn service delete --all"
        result = subprocess.run(delete_service_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(f"kn service delete command completed with return code {result.returncode}")
    except subprocess.CalledProcessError as e:
        log.warning(f"Services not deleted. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
        return -1
    except Exception as e:
        log.warning(f"Services not deleted. Error: {e}")
        return -1
    
    # Monitor the service list whether everything is deleted. Wait until all the services are deleted.
    def are_services_deleted() -> bool:
        try:
            get_servicelist_command = f"kn service list --no-headers"
            result = subprocess.run(get_servicelist_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            services = result.stdout.decode('utf-8').strip().split('\n')
            services = [s for s in services if s != '']
            for s in services:
                if "No services found." in s: return True
            else: return False 
        except subprocess.CalledProcessError as e:
            log.warning(f"Service List can't be monitored. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            log.warning(f"Service List can't be monitored. Error: {e}")
            return False

    # Monitor the service list, until all are deleted.
    # Monitoring happens every 1 second for 15 minutes. If it shows failure even after that then it returns failure
    monitor_time = 15 * 60
    sleep_time = 1
    status = False
    for _ in range(int(monitor_time / sleep_time)):
        status = are_services_deleted()
        if status: break
        else: time.sleep(sleep_time)

    if status:
        log.info(f"All services deleted")
        return 0
    else:
        log.warning(f"Services not deleted")
        return -1




def deploy_metrics_server(metrics_server_yaml_location: str) -> int:

    # Deploy the metrics server
    try:
        deployment_command = f"kubectl apply -f {metrics_server_yaml_location}"
        subprocess.run(deployment_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        log.warning(f"Metrics Server not deployed. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
        return -1
    except Exception as e:
        log.warning(f"Metrics Server not deployed. Error: {e}")
        return -1

    # Get the pod status of metrics server
    def monitor_pods_to_check_metrics_server_deployed() -> int:
        try:
            get_podlist_command = f"kubectl get pods --all-namespaces --no-headers"
            result = subprocess.run(get_podlist_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pods = result.stdout.decode('utf-8').strip().split('\n')
            for p in pods:
                # TODO: Can this be done better?
                if (("metrics-server" in p) and (p.split()[3] == "Running")):
                    return True
            return False
        except subprocess.CalledProcessError as e:
            log.warning(f"Metrics Server deployment can't be monitored. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            log.warning(f"Metrics Server deployment can't be monitored. Error: {e}")
            return False

    # Monitor the pod list, until it is ready
    # Monitoring happens every 5 seconds for 15 minutes. If it shows failure even after that then it returns failure
    monitor_time = 15 * 60
    sleep_time = 5
    status = False
    for _ in range(int(monitor_time / sleep_time)):
        status = monitor_pods_to_check_metrics_server_deployed()
        if status: break
        else: time.sleep(sleep_time)

    if status:
        log.info(f"Metrics server deployed")
        return 0
    else:
        log.warning(f"Metrics server not deployed")
        return -1



def get_metrics_server_data(function_name: str, run_duration: float, sample_time_period: float, memory_txt_location: str, cpu_txt_location: str) -> Tuple[str, list, list, int]:
    
    # Get the pod name for the given function name
    def get_pod_name(function_name: str) -> Tuple[str, int]:
        get_podlist_command = f"kubectl get pods --no-headers"
        try:
            result = subprocess.run(get_podlist_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pods = result.stdout.decode('utf-8').strip().split('\n')
            for p in pods:
                # TODO:Can this be done better?
                if ((function_name in p) and (p.split()[2] == "Running")):
                    return p.split()[0], 0
            return None, -1
        except subprocess.CalledProcessError as e:
            log.warning(f"Pod List can't be obtained. Metrics Server Data failed. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
            return None, -1
        except Exception as e:
            log.warning(f"Pod List can't be obtained. Metrics Server Data failed. Error: {e}")
            return None, -1
    
    # Given the pod name, find the CPU and memory utilization of the pod
    def _get_metrics_server_data(pod_name: str) -> Tuple[str, str, int]:
        get_stat_command = f"kubectl top pod {pod_name} --no-headers"
        try:     
            result = subprocess.run(get_stat_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pods = result.stdout.decode('utf-8').strip().split('\n')  
            for p in pods:
                if pod_name in p:
                    cpu = p.split()[1]
                    memory = p.split()[2]
                    return cpu, memory, 0
            return None, None, -1
        except subprocess.CalledProcessError as e:
            log.warning(f"Metrics Server. kubectl top command failed. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
            return None, None, -1
        except Exception as e:
            log.warning(f"Metrics Server. kubectl top command failed. Error: {e}")
            return None, None, -1
    
    # Monitor the pod list, until pod name is obtained
    # Monitoring happens every 5 seconds for 15 minutes. If it shows failure even after that then it returns failure
    monitor_time = 15 * 60
    sleep_time = 5
    status = False
    for _ in range(int(monitor_time / sleep_time)):
        pod_name, err = get_pod_name(function_name)
        if (err == 0): 
            status = True
            break
        else: 
            status = False
            time.sleep(sleep_time)

    if status:
        log.info(f"function {function_name}: Pod details obtained. Pod: {pod_name}")
    else:
        log.warning(f"Pod Details can't be obtained for function {function_name}. Metrics Server Data not obtained")
        return "", [], [], -1


    cpu = []            # Store CPU usage details over samples
    memory = []         # Store memory usage details over samples

    # Get the CPU and memory usage details and store it in a list
    for _ in range(int(run_duration / sample_time_period)):
        c, m, err = _get_metrics_server_data(pod_name)
        if err != -1:
            cpu.append(c)
            memory.append(m)
        time.sleep(sample_time_period)

    # Write the memory utilization data to memory.txt
    # Check whether folder where the memory.txt are to be located exists or not
    if not os.path.exists(memory_txt_location):
        log.info(f"{memory_txt_location} directory does not exist.")
        os.makedirs(memory_txt_location)
        log.info(f"{memory_txt_location} directory created")
    else: pass
    with open(f"{memory_txt_location}/memory.txt", 'w') as f:
        for m in memory:
            f.write(str(m) + '\n') 

    # Write the cpu utilization data to cpu.txt
    # Check whether folder where the cpu.txt are to be located exists or not
    if not os.path.exists(cpu_txt_location):
        log.info(f"{cpu_txt_location} directory does not exist.")
        os.makedirs(cpu_txt_location)
        log.info(f"{cpu_txt_location} directory created")
    else: pass
    with open(f"{cpu_txt_location}/cpu.txt", 'w') as f:
        for c in cpu:
            f.write(str(c) + '\n') 

    log.info(f"{function_name}: {pod_name}: CPU & Memory utilization details written in {memory_txt_location}/memory.txt and  {cpu_txt_location}/cpu.txt")
    return pod_name, cpu, memory, 0




# Run invoker command
def run_invoker(invoker_location: str, endpoints_location: str, latency_txt_location: str, invoker_output_location: str, rps: float, run_duration: float) -> int:
    try:
        log.info(f"Function Invocation started. Data is getting collected")
        run_invoker_command = f"sudo {invoker_location}/invoker -port=80 -time={run_duration} -rps={rps} -dbg=true -endpointsFile='{endpoints_location}/endpoints.json' -latf='{latency_txt_location}/latency.txt' > {invoker_output_location}/invoker.log"
        result = subprocess.run(run_invoker_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(f"Invoker command completed with return code: {result.returncode}")
    except subprocess.CalledProcessError as e:
        log.warning(f"Invoker command failed Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
        return -1
    except Exception as e:
        log.warning(f"Invoker command failed. Error: {e}")
        return -1
    log.info(f"Function invocation successfully executed")
    return 0



def collect_stats(function_name: str, yaml_filename: str, latency_txt_location: str, memory_txt_location: str, cpu_txt_location: str) -> Tuple[dict, int]:
    
    def get_average_percentile(numbers: list, percentile_list: list):
        numbers.sort()
        average = []
        for i in range(len(numbers)):
            sub_array = numbers[:i+1]
            average.append(sum(sub_array) / len(sub_array))
        percentiles = np.percentile(average, percentile_list)
        return percentiles
            
    def latency_stats(latency_txt_location: str, percentile_list: list) -> Tuple[list, int]:
        try:
            with open(f"{latency_txt_location}/latency.txt",'r') as f:
                latency = [float(line.strip()) for line in f]
                latency_percentiles = get_average_percentile(latency, percentile_list)
                return latency_percentiles, 0
        except FileNotFoundError:
            log.warning(f"{latency_txt_location}/latency.txt File not found")
            return [], -1
        except Exception as e:
            log.warning(f"{latency_txt_location}/latency.txt File. Error: {e}")
            return [], -1

    def memory_stats(memory_txt_location: str, percentile_list: list) -> Tuple[list, int]:
        try:
            with open(f"{memory_txt_location}/memory.txt",'r') as f:
                memory = [float(line.strip()[:-2]) for line in f]
                memory_percentiles = get_average_percentile(memory, percentile_list)
                return memory_percentiles, 0
        except FileNotFoundError:
            log.warning(f"{memory_txt_location}/memory.txt File not found")
            return [], -1
        except Exception as e:
            log.warning(f"{memory_txt_location}/memory.txt File. Error: {e}")
            return [], -1

    def cpu_stats(cpu_txt_location: str, percentile_list: list) -> Tuple[list, int]:
        try:
            with open(f"{cpu_txt_location}/cpu.txt",'r') as f:
                cpu = [float(line.strip()[:-1]) for line in f]
                cpu_percentiles = get_average_percentile(cpu, percentile_list)
                return cpu_percentiles, 0
        except FileNotFoundError:
            log.warning(f"{cpu_txt_location}/cpu.txt File not found")
            return [], -1
        except Exception as e:
            log.warning(f"{cpu_txt_location}/cpu.txt File. Error: {e}")
            return [], -1

    function = {}
    function['name'] = function_name 
    function['yaml'] = yaml_filename
    function['cpu'] = {}
    function['memory'] = {}
    function['latency'] = {}

    percentile_list = [0, 1, 5, 25, 50, 75, 95, 99, 100]
    e = 0

    memory_percentiles, err = memory_stats(memory_txt_location, percentile_list)   
    if err != 0:
        log.warning(f"function {function_name} memory stats not collected")
        e = -1
    else:
        log.info(f"function {function_name} memory stats collected")
        for p in percentile_list: function['memory'][f'{p}-percentile'] = memory_percentiles[percentile_list.index(p)]

    latency_percentiles, err = latency_stats(latency_txt_location, percentile_list)   
    if err != 0:
        log.warning(f"function {function_name} latency stats not collected")
        e = -1
    else:
        log.info(f"function {function_name} latency stats collected")
        for p in percentile_list: function['latency'][f'{p}-percentile'] = latency_percentiles[percentile_list.index(p)]

    cpu_percentiles, err = cpu_stats(cpu_txt_location, percentile_list)   
    if err != 0:
        log.warning(f"function {function_name} cpu stats not collected")
        e = -1
    else:
        log.info(f"function {function_name} cpu stats collected")
        for p in percentile_list: function['cpu'][f'{p}-percentile'] = cpu_percentiles[percentile_list.index(p)]

    log.info(f"function {function_name} statistics collected")
    return function, e


def wait_until_pod_is_deleted(pod_name: str) -> int:
    
    def is_pod_deleted(pod_name: str) -> bool:
        get_podlist_command = f"kubectl get pods --no-headers"
        try:
            result = subprocess.run(get_podlist_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pods = result.stdout.decode('utf-8').strip().split('\n')
            for p in pods:
                # TODO:Can this be done better?
                if (pod_name in p):
                    return False
            return True
        except subprocess.CalledProcessError as e:
            log.warning(f"Pod List can't be obtained. I don't know whether pod {pod_name} is deleted or not. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            log.warning(f"Pod List can't be obtained. I don't know whether pod {pod_name} is deleted or not. Error: {e}")
            return False

    # Monitor the pod list, until the pod is deleted.
    # Monitoring happens every 5 seconds for 15 minutes. If it shows failure even after that then it returns failure
    monitor_time = 15 * 60
    sleep_time = 5
    status = False
    for _ in range(int(monitor_time / sleep_time)):
        status = is_pod_deleted(pod_name)
        if status: break
        else: time.sleep(sleep_time)

    if status:
        log.info(f"Pod {pod_name} deleted")
        return 0
    else:
        log.warning(f"Pod {pod_name} not deleted")
        return -1



check_shell_path()
deploy_metrics_server("metrics-server/components.yaml")
delete_all_services()


yaml_name = "kn-aes-go"
function_name, _ = deploy_service(f"yamls/{yaml_name}.yaml", [], [], f"build/{yaml_name}")
endpoint, _ = get_endpoint(function_name, ".")

rps = 0.2
run_duration = 90
sample_time_period = 10

run_invoker_in_background = threading.Thread(target=run_invoker, args=(".", ".", f"build/{yaml_name}", f"build/{yaml_name}", rps, run_duration))
run_invoker_in_background.start()

time.sleep(10)
pod_name, cpu, memory, _ = get_metrics_server_data(function_name, run_duration, sample_time_period, f"build/{yaml_name}", f"build/{yaml_name}") 

run_invoker_in_background.join()

function = collect_stats(function_name, yaml_name, f"build/{yaml_name}", f"build/{yaml_name}", f"build/{yaml_name}")
print(function)

wait_until_pod_is_deleted(pod_name)
delete_all_services()



