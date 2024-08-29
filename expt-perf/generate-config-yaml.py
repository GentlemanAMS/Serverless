import yaml

template_yaml = """
output-files-path: {output_files_path}
log-files-path: {log_files_path}

load-generator:
  deploy: true
  python_file: /users/Lakshman/vSwarm/tools/load-generator/main.py
  load_json: /users/Lakshman/vSwarm/tools/load-generator/load.json
  trace_path: /users/Lakshman/vSwarm/tools/load-generator/{trace_path}
  profile_json: /users/Lakshman/vSwarm/tools/load-generator/profile.json
  config_json: /users/Lakshman/vSwarm/tools/load-generator/config.json
  build_path: /users/Lakshman/vSwarm/tools/load-generator/build
  expt_dur: {load_expt_dur}
  warmup_dur: {load_warmup_dur}

invoke-load:
  run: true
  binary_path: /users/Lakshman/vSwarm/tools/load-generator/invoker
  log_file: invoker-load.log
  expt_dur: {load_expt_dur}
  warmup_dur: {load_warmup_dur}

profile-service:
  deploy: true
  yaml_path: {yaml_path}
  predeployment_commands: [{predeployment_command}]
  postdeployment_commands: []
  endpoints_file: endpoints.json  

invoke-service:
  run: true
  binary_path: .
  log_file: invoker-service.log
  dur_file: dur.txt
  lat_file: lat.txt
  expt_dur: {service_expt_dur}
  rps: {rps}

taskset-service:
  set: true
  cpuid: 2

perf:
  collect: true
  grep_string: \"{grep_string}\"
  event_list:
    - CPU_CLK_UNHALTED.THREAD
    - INST_RETIRED.ANY

  expt_dur: {stat_expt_dur}
  interval_print_ms: {stat_interval_print_ms}
  warmup_dur: {stat_warmup_dur}
  output_file: perf.txt

mpstat:
  collect: true
  expt_dur: {stat_expt_dur}
  warmup_dur: {stat_warmup_dur}
  interval: 60
  output_file: mpstat.txt
"""



trace_path = [10,200,450]
function_name="video-processing-python-1500"
yaml_path = "/users/Lakshman/vSwarm/tools/load-generator/yamls/video-processing/kn-video-processing-python-1500.yaml"
grep_string = "python3 /app/server.py"
predeployment_command = "kubectl apply -f /users/Lakshman/vSwarm/tools/load-generator/yamls/video-processing/video-processing-database.yaml"
load_expt_dur = 4
load_warmup_dur = 1
service_expt_dur = load_expt_dur + load_warmup_dur
rps=0.2
stat_expt_dur = load_expt_dur - 1
stat_warmup_dur = load_warmup_dur
stat_interval_print_ms = 250

for i in range(len(trace_path)):

    file_name=f"config-{function_name}-{trace_path[i]}.yaml"
    output_files_path = f"{function_name}-{trace_path[i]}"
    log_files_path = f"{function_name}-{trace_path[i]}" 

    yaml_content = template_yaml.format(
        output_files_path=output_files_path,
        log_files_path=log_files_path,
        trace_path=trace_path[i],
        load_expt_dur=load_expt_dur,
        load_warmup_dur=load_warmup_dur,
        yaml_path=yaml_path,
        predeployment_command=predeployment_command,
        service_expt_dur=service_expt_dur,
        rps=rps,
        grep_string=grep_string,
        stat_expt_dur=stat_expt_dur,
        stat_warmup_dur=stat_warmup_dur,
        stat_interval_print_ms=stat_interval_print_ms
      )

    with open(file_name, "w") as f:
        f.write(yaml_content)

