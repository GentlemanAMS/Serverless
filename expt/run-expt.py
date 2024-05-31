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


def delete_all_services():

    # Delete all the services
    try:
        delete_service_command = f"kn service delete --all"
        result = subprocess.run(
            delete_service_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        log.info(
            f"kn service delete command completed with return code {result.returncode}"
        )
    except subprocess.CalledProcessError as e:
        log.warning(
            f"Services not deleted. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}"
        )
        return -1
    except Exception as e:
        log.warning(f"Services not deleted. Error: {e}")
        return -1

    # Monitor the service list whether everything is deleted. Wait until all the services are deleted.
    def are_services_deleted() -> bool:
        try:
            get_servicelist_command = f"kn service list --no-headers"
            result = subprocess.run(
                get_servicelist_command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            services = result.stdout.decode("utf-8").strip().split("\n")
            services = [s for s in services if s != ""]
            for s in services:
                if "No services found." in s:
                    return True
            return False
        except subprocess.CalledProcessError as e:
            log.warning(
                f"Service List can't be monitored. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}"
            )
            return False
        except Exception as e:
            log.warning(f"Service List can't be monitored. Error: {e}")
            return False

    # Monitor the service list, until all are deleted.
    # Monitoring happens every 2 second for 15 minutes. If it shows failure even after that then it returns failure
    monitor_time = 15 * 60
    sleep_time = 2
    status = False
    for _ in range(int(monitor_time / sleep_time)):
        status = are_services_deleted()
        if status:
            break
        else:
            time.sleep(sleep_time)

    if status:
        log.info(f"All services deleted")
        return 0
    else:
        log.warning(f"Services not deleted.")
        return -1


def deploy_load(python_file, build_path, load_file, trace_path, profile_path, config_path, expt_dur, warmup_dur):
    command = ["python3", f"{python_file}", "loadgen", "-b", f"{build_path}", "-o", f"{load_file}", "-t", f"{trace_path}", "-p", f"{profile_path}", "-c", f"{config_path}", "-m", "True", "-u", "False", "-i", "equidistant", "-d", f"{expt_dur}", "-w", f"{warmup_dur}"]

    try:
        # Execute the command and wait for it to complete
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)  
        # Successful execution
        log.info(f"Load generated and deployed successfully")
                
    except Exception as e:
        # Handles other exceptions such as FileNotFoundError, etc.
        log.critical(f"An error occurred while generating and deploying the load: {e}")


def invoke_load(invoker_loc, expt_dur, warmup_dur, load_file, log_file):
    command = f"{invoker_loc}/invoker -duration={expt_dur} -dbg=true -min=true -traceFile={load_file} -warmup={warmup_dur} >> {log_file}"
    try:
        log.info(f"invoker command: {command}")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(f"Load is getting invoked. Command started asynchronously. PID: {process.pid}")
        
    except Exception as e:
        log.critical(f"An error occurred while starting the invocation: {e}")



def deploy_service(yaml_path, predeployment_commands, postdeployment_commands, build_path):

    # Check whether yaml file exists or not.
    try:
        with open(yaml_path, "r"):
            pass
    except FileNotFoundError:
        log.critical(f"{yaml_path} YAML file not found")
        return None
    except Exception as e:
        log.critical(f"{yaml_path} YAML file can't be opened. Error occured: {e}")
        return None

    # Get the function name from yaml file
    yaml_function_name = None
    try:
        with open(yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f)
            yaml_function_name = yaml_data["metadata"]["name"]
    except KeyError as e:
        log.error(f"Function name not found. KeyError:{e}. Switching to default name: function")
        return None
    except Exception as e:
        log.critical(f"{yaml_path} YAML File can't be opened. An error occured: {e}")
        return None
    
    # Creating a service, yaml file whose service name is unique
    characters = string.ascii_lowercase + string.digits
    random_string = "".join(secrets.choice(characters) for _ in range(7))
    yaml_function_name = yaml_function_name + "-" + random_string
    yaml_data["metadata"]["name"] = yaml_function_name

    basename = os.path.basename(yaml_path).replace(".yaml", "")
    modified_yaml_filename = basename + "-" + random_string + ".yaml"
    modified_yaml_filename = f"{build_path}/{modified_yaml_filename}"

    # The modified yaml file is then stored in build directory
    try:
        with open(modified_yaml_filename, "w") as yf:
            yaml.dump(yaml_data, yf, default_flow_style=False)
    except Exception as e:
        log.error( f"Error occured while creating the YAML file. {yaml_path}: {modified_yaml_filename} not deployed" )
        return None

        # Create a list of commands to be executed
    commands = []
    # Commands to be executed before deployment
    for c in predeployment_commands:
        commands.append(c + "\n")
    # Deployment command
    deployment_command = f"kubectl apply -f {modified_yaml_filename}"
    commands.append(deployment_command + "\n")
    # Commands to be executed after deployment
    for c in postdeployment_commands:
        commands.append(c + "\n")
    
    # Get shell path
    shell_path = os.environ.get("SHELL")

    # Writing a shell script
    # Creating the shell script file name
    shell_filename = basename + "-" + random_string + ".sh"
    shell_filename = f"{build_path}/{shell_filename}"
    # Writing commands into the shell script
    with open(shell_filename, "w") as f:
        f.write(f"#!{shell_path}\n")
        for c in commands:
            f.write(c)
    # Setting executable permissions for the shell script
    # Permissions: -rwxr-xr-x
    os.chmod(
        shell_filename,
        stat.S_IRUSR
        | stat.S_IWUSR
        | stat.S_IXUSR
        | stat.S_IRGRP
        | stat.S_IXGRP
        | stat.S_IROTH
        | stat.S_IXOTH,
    )
    log.debug(f"{shell_filename} created")    


    # Execute the shell script and deploy the function
    execute_shell = f"{shell_path} {shell_filename}"
    try:
        result = subprocess.run(
            execute_shell,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        log.debug(
            f"{shell_filename} executed successfully with return code: {result.returncode}"
        )
        log.info(
            f"{yaml_path}: {modified_yaml_filename} service deployed"
        )
    except subprocess.CalledProcessError as e:
        log.error(
            f"{shell_filename} execution failed. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}"
        )
        return None
    except Exception as e:
        log.error(f"{shell_filename} execution failed. Error: {e}")
        return None


    def get_service_status(function_name: string) -> bool:
        try:
            get_service_command = f"kn service list --no-headers"
            result = subprocess.run(
                get_service_command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            services = result.stdout.decode("utf-8").strip().split("\n")

            for s in services:
                try:
                    name = s.split()[0]
                    status = s.split()[8]
                except IndexError:
                    continue
                if function_name in name:
                    if status == "True":
                        return True
                    else:
                        continue
            return False

        except subprocess.CalledProcessError as e:
            log.warning(
                f"Service can't be monitored. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}"
            )
            return False
        except Exception as e:
            log.warning(f"Service can't be monitored. Error: {e}")
            return False

    monitor_time = 60 * 5
    sleep_time = 15
    status = False
    for _ in range(int(monitor_time / sleep_time)):
        status = get_service_status(yaml_function_name)
        if status:
            break
        else:
            time.sleep(sleep_time)

    if status:
        log.info(
            f"Service: {yaml_function_name} deployed successfully"
        )
        return yaml_function_name
    else:
        log.error(
            f"Service: {yaml_function_name} NOT deployed successfully"
        )
        return None




def collect_endpoint(yaml_function_name, endpoint_file_location):

    get_service_command = f"kn service list --no-headers"
    try:
        result = subprocess.run(
            get_service_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = result.stdout.decode("utf-8").strip().split("\n")
    except subprocess.CalledProcessError as e:
        log.error(
            f"Endpoints can't be collected. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}"
        )
        return None
    except Exception as e:
        log.warning(f"Endpoints can't be collected. Error: {e}")
        return None
    
    yaml_function_name_endpoint = None
    for r in result:
        try:
            service_name = r.split()[0]
            endpoint = r.split()[1].replace("http://", "")
            if service_name == yaml_function_name:
                yaml_function_name_endpoint = endpoint
                log.info(f"Endpoint of {yaml_function_name} found: {endpoint}")
                break
        except IndexError:
            continue
        except Exception as e:
            log.warning(f"Error trying to find the correct endpoint : {e}")
            continue
    
    if yaml_function_name_endpoint == None:
        log.error(f"Endpoint for function: {yaml_function_name} NOT found")
        return None
    
    endpoint = yaml_function_name_endpoint
    endpoint = [{"hostname": endpoint}]
    json_output = json.dumps(endpoint, indent=3)

    json_file = open(f"{endpoint_file_location}", "w")
    json_file.write(json_output)
    json_file.close()
    log.debug(f"{endpoint_file_location} file written")

    return yaml_function_name


def run_invoker(invoker_loc, endpoint_file_location, rps, expt_dur, lat_file, dur_file, log_file):
    command = f"{invoker_loc}/invoker -time={expt_dur} -profile=true -durf={dur_file} -latf={lat_file} -endpointsFile={endpoint_file_location} -rps={rps} >> {log_file}"
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(f"Invoker is invoking the function of interest. Command started asynchronously. PID: {process.pid}")
        
    except Exception as e:
        log.critical(f"An error occurred while invoking the function of interest: {e}")


def get_pod_name(yaml_function_name):
    
    try:
        result = subprocess.run(["kubectl","get","pods"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            command_result = result.stdout
        else:
            log.error(f"Error in finding the pod-name: {result.stderr}")
            return None
    except subprocess.CalledProcessError as e:
        log.error(f"Error in finding the pod-name: {e}")
        return None

    command_result = command_result.split('\n')
    command_result = command_result[1:]     # Removing header
    # command_result = command_result[:-2]    # Removing last endline - empty line

    for line in command_result:
        try:
            line = line.split()
            pod_name = line[0]
            # pod_status = line[2]
            # pod_age = line[4]
            if yaml_function_name in pod_name:
                log.info(f"Pod name for {yaml_function_name} found: {pod_name}")
                return pod_name
        except Exception as e:
            continue

    log.error(f"Pod name for {yaml_function_name} NOT found")        
    return None






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
    



def run_perf(event_list, pid, warmup_dur, expt_dur, output_file):

    run_perf_command = f"sudo perf stat -e "
    for i in range(len(event_list)):
        run_perf_command += f"{event_list[i]}"
        if i != len(event_list)-1: run_perf_command += f","
    run_perf_command += f" -p {pid}"
    run_perf_command += f" --delay {warmup_dur}"
    run_perf_command += f" -o {output_file}"
    run_perf_command += f" --timeout {expt_dur}"

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


def delete_service(function_name):

    # Delete all the services
    try:
        delete_service_command = f"kn service delete {function_name}"
        result = subprocess.run(
            delete_service_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        log.info(
            f"kn service delete {function_name} command completed with return code {result.returncode}"
        )
    except subprocess.CalledProcessError as e:
        log.warning(
            f"Services not deleted. Return code: {e.returncode}. Error: {e.stderr.decode('utf-8')}"
        )
        return -1
    except Exception as e:
        log.warning(f"Services not deleted. Error: {e}")
        return -1


import argparse
parser = argparse.ArgumentParser(description="Perf analysis.")
parser.add_argument("-c","--config",metavar="path",required=False, default="config.yaml")
args = parser.parse_args()
filename = args.config

with open(filename, 'r') as file:
  try:
    config_data = yaml.safe_load(file)
  except yaml.YAMLError as exc:
    log.critical(f"Error loading YAML file: {exc}")
    sys.exit(0)

if not os.path.exists(config_data['output-files-path']):
    os.makedirs(config_data['output-files-path'])
if not os.path.exists(config_data['log-files-path']):
    os.makedirs(config_data['log-files-path'])

if (config_data['load-generator']['deploy'] == True):
    delete_all_services()
    deploy_load(
        python_file=config_data['load-generator']['python_file'],
        build_path=config_data['load-generator']['build_path'], 
        load_file=config_data['load-generator']['load_json'], 
        trace_path=config_data['load-generator']['trace_path'], 
        profile_path=config_data['load-generator']['profile_json'], 
        config_path=config_data['load-generator']['config_json'], 
        expt_dur=config_data['load-generator']['expt_dur'], 
        warmup_dur=config_data['load-generator']['warmup_dur']
    )

if(config_data['profile-service']['deploy']): 
    function_name = deploy_service(
        yaml_path=config_data['profile-service']['yaml_path'], 
        predeployment_commands=config_data['profile-service']['predeployment_commands'], 
        postdeployment_commands=config_data['profile-service']['postdeployment_commands'], 
        build_path=config_data['log-files-path']
    )

    endpoint = collect_endpoint(
        yaml_function_name=function_name, 
        endpoint_file_location=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}"
    )
    endpoint_iter = 0
    while (endpoint == None):
        endpoint = collect_endpoint(
            yaml_function_name=function_name, 
            endpoint_file_location=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}"
        )
        time.sleep(15)
        endpoint_iter += 1
        if (endpoint_iter == 30): 
            sys.exit()

time.sleep(10)

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

# time.sleep(20)

pod_name = get_pod_name(function_name)
pod_name_iter = 0
while (pod_name == None):
    pod_name = get_pod_name(function_name)
    time.sleep(15)
    pod_name_iter += 1
    if (pod_name_iter == 30): 
        break


pid = get_pid(pod_name=pod_name, grep_string=config_data['perf']['grep_string'])

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
        output_file=f"{config_data['output-files-path']}/{config_data['perf']['output_file']}"
    )

time.sleep(90)

if(config_data['profile-service']['deploy']): 
    delete_service(function_name)



