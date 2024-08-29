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
parser = argparse.ArgumentParser(description="Perf analysis")
parser.add_argument("-iIP","--invokerIP",required=True)
parser.add_argument("-iPORT","--invokerPORT",required=True)
parser.add_argument("-iHOST","--invokerHOSTNAME",required=False, default="Lakshman")
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

invoker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
invoker_server_address = (args.invokerIP, int(args.invokerPORT))
invoker_sock.connect(invoker_server_address)

perfer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
perfer_server_address = (args.perfIP, int(args.perfPORT))
perfer_sock.connect(perfer_server_address)




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
        return 0
                
    except Exception as e:
        # Handles other exceptions such as FileNotFoundError, etc.
        log.critical(f"An error occurred while generating and deploying the load: {e}")
        return -1


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
        log.critical(
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
    log.info(f"{endpoint_file_location} file written")

    return endpoint


def send_file_via_scp(server_ip, username, file_path, remote_path):

    try:
        # Construct the SCP command
        # scp_command = [
        #     'scp', '-r',
        #     file_path,
        #     f'{username}@{server_ip}:{remote_path}'
        # ]
        scp_command = f"scp -i ~/.ssh/id_ed25519 -r {file_path} {username}@{server_ip}:{remote_path}"

        # Run the SCP command using subprocess
        _ = subprocess.run(
            scp_command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )
        
        log.info(f"{file_path} successfully sent to invoker node: {username}@{server_ip}:{remote_path}")
        return 0

    except subprocess.CalledProcessError as e:
        log.error(f"An error occurred while sending {file_path} to invoker node {username}@{server_ip}:{remote_path}. Error: {e.stderr}")
        return -1


def send_start_invocation_command_to_invoker(sock, config_filename):
    try:
        command = f"START INVOKER. CONFIG: {config_filename}"        
        message = command.encode()
        sock.sendall(message)
        log.info(f"'{command}' sent to invoker")
        return 0

    except Exception as e:
        log.error(f"An error occurred while sending command '{command}' to invoker. Error: {e}")
        return -1


def wait_for_reply_from_invoker_for_start_command(sock, config_filename):
    try:
        while True:
            data = sock.recv(1024)
            if data:
                received_string = data.decode()
                if f"START INVOKER. SUCCESS {config_filename}" in received_string:
                    log.info(f"Invoker replied SUCCESS to START INVOKER COMMAND")
                    return 0
                elif f"START INVOKER. FAILED {config_filename}" in received_string:
                    log.critical(f"Invoker replied FAILED to START INVOKER COMMAND")
                    return -1
    except Exception as e:
        log.critical(f"Master did not receive reply from invoker for START INVOKER COMMAND. Error: {e}")



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



def send_start_perf_command_to_perfer(sock, pod_name, config_filename):
    try:
        command = f"START PERFER. CONFIG: {config_filename} POD: {pod_name}"        
        message = command.encode()
        sock.sendall(message)
        log.info(f"'{command}' sent to perfer")
        return 0
    except Exception as e:
        log.error(f"An error occurred while sending command '{command}' to perfer. Error: {e}")
        return -1


def wait_for_perf_to_complete(sock, config_filename):

    try:
        while True:
            data = sock.recv(1024)
            if data:
                received_string = data.decode()
                if f"PERF COMPLETED. SUCCESS {config_filename}" in received_string:
                    log.info(f"Perfer replied SUCCESS to START PERFER COMMAND")
                    return 0
                elif f"PERF COMPLETED. FAILED {config_filename}" in received_string:
                    log.critical(f"Perfer replied FAILED to START PERFER COMMAND")
                    return -1
    except Exception as e:
        log.critical(f"Master did not receive reply from perfer for START PERFER COMMAND. Error: {e}")


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








for filepath in yaml_files:

    with open(filepath, 'r') as file:
        try:
            config_data = yaml.safe_load(file)
        except Exception as e:
            log.critical(f"Error loading YAML file: {e}")
            continue

    if not os.path.exists(config_data['output-files-path']):
        os.makedirs(config_data['output-files-path'])
        os.chmod(config_data['output-files-path'], stat.S_IRWXO)
    if not os.path.exists(config_data['log-files-path']):
        os.makedirs(config_data['log-files-path'])
        os.chmod(config_data['log-files-path'], stat.S_IRWXO)

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
        if function_name is None:
            continue

        endpoint = collect_endpoint(
            yaml_function_name=function_name, 
            endpoint_file_location=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}"
        )
        endpoint_iter = 0
        while endpoint is None:
            endpoint = collect_endpoint(
                yaml_function_name=function_name, 
                endpoint_file_location=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}"
            )
            time.sleep(15)
            endpoint_iter += 1
            if (endpoint_iter == 30): 
                log.critical(f"Endpoint for function {function_name} NOT found")
                if(config_data['profile-service']['deploy']):  delete_service(function_name)
                break
        if endpoint is None: continue

    e = send_file_via_scp(
        server_ip=args.invokerIP,
        username=args.invokerHOSTNAME,
        file_path=config_data['load-generator']['load_json'],
        remote_path=config_data['load-generator']['load_json']
    )
    scp_iter = 0
    while e == -1:
        e = send_file_via_scp(
            server_ip=args.invokerIP,
            username=args.invokerHOSTNAME,
            file_path=config_data['load-generator']['load_json'],
            remote_path=config_data['load-generator']['load_json']
        )
        scp_iter += 1
        time.sleep(2)
        if (scp_iter == 30):
            log.critical(f"An error occurred while sending load.json to invoker node {args.invokerHOSTNAME}@{args.invokerIP}")
            if(config_data['profile-service']['deploy']):  delete_service(function_name)
            break
    if e == -1: continue
            

    e = send_file_via_scp(
        server_ip=args.invokerIP,
        username=args.invokerHOSTNAME,
        file_path=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}",
        remote_path=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}"
    )
    scp_iter = 0
    while e == -1:
        e = send_file_via_scp(
            server_ip=args.invokerIP,
            username=args.invokerHOSTNAME,
            file_path=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}",
            remote_path=f"{config_data['log-files-path']}/{config_data['profile-service']['endpoints_file']}"
        )
        scp_iter += 1
        time.sleep(2)
        if (scp_iter == 30):
            log.critical(f"An error occurred while sending endpoints.json to invoker node {args.invokerHOSTNAME}@{args.invokerIP}")
            if(config_data['profile-service']['deploy']):  delete_service(function_name)
            break
    if e == -1: continue



    e = send_start_invocation_command_to_invoker(
        sock=invoker_sock,
        config_filename=filepath
    )
    comm_iter = 0
    while e == -1:
        e = send_start_invocation_command_to_invoker(
            sock=invoker_sock,
            config_filename=filepath
        )
        comm_iter += 1
        time.sleep(2)
        if (comm_iter == 30):
            log.critical(f"An error occurred while sending START INVOKER command to invoker {args.invokerIP}:{int(args.invokerPORT)}")
            if(config_data['profile-service']['deploy']):  delete_service(function_name)
            break
    if e == -1: continue


    start_time = time.time()
    time_to_sleep = max(config_data['invoke-service']['expt_dur']*60, (config_data['invoke-load']['expt_dur'] + config_data['invoke-load']['warmup_dur'])*60)


    e = wait_for_reply_from_invoker_for_start_command(
        sock=invoker_sock,
        config_filename=filepath
    )
    if e == -1:
        time.sleep(config_data['invoke-service']['expt_dur']*60)
        if(config_data['profile-service']['deploy']):  delete_service(function_name)
        time_difference = time.time() - start_time
        if (time_difference < time_to_sleep): time.sleep(time_to_sleep - time_difference)
        continue

    time.sleep(50)

    pod_name = get_pod_name(function_name)
    pod_name_iter = 0
    while pod_name is None:
        pod_name = get_pod_name(function_name)
        pod_name_iter += 1
        time.sleep(15)
        if (pod_name_iter == 30): 
            time.sleep(config_data['invoke-service']['expt_dur']*60)
            if(config_data['profile-service']['deploy']):  delete_service(function_name)
            time_difference = time.time() - start_time
            if (time_difference < time_to_sleep): time.sleep(time_to_sleep - time_difference)
            break
    if pod_name is None: continue


    e = send_start_perf_command_to_perfer(
        pod_name=pod_name,
        sock=perfer_sock,
        config_filename=filepath
    )
    comm_iter = 0
    while e == -1:
        e = send_start_perf_command_to_perfer(
            pod_name=pod_name,
            sock=perfer_sock,
            config_filename=filepath
        )
        comm_iter += 1
        time.sleep(2)
        if (comm_iter == 30):
            log.critical(f"An error occurred while sending START PERFER command to perfer {args.perfIP}:{int(args.perfPORT)}")
            if(config_data['profile-service']['deploy']):  delete_service(function_name)
            time_difference = time.time() - start_time
            if (time_difference < time_to_sleep): time.sleep(time_to_sleep - time_difference)
            break
    if e == -1: continue


    e = wait_for_perf_to_complete(
        sock=perfer_sock,
        config_filename=filepath
    )
    if e == -1:
        time.sleep(config_data['invoke-service']['expt_dur']*60)
        log.critical(f"MASTER did not receive perf complete successfully message")
        if(config_data['profile-service']['deploy']):  delete_service(function_name)

    time_difference = time.time() - start_time
    time_to_sleep = max(config_data['invoke-service']['expt_dur']*60, (config_data['invoke-load']['expt_dur'] + config_data['invoke-load']['warmup_dur'])*60)
    if (time_difference < time_to_sleep): time.sleep(time_to_sleep - time_difference)

    if(config_data['profile-service']['deploy']): 
        delete_service(function_name)

invoker_sock.close()
perfer_sock.close()

