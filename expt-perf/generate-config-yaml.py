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
  deploy: false
  yaml_path: {yaml_path}
  predeployment_commands: [{predeployment_command}]
  postdeployment_commands: []
  endpoints_file: endpoints.json  

invoke-service:
  run: false
  binary_path: .
  log_file: invoker-service.log
  dur_file: dur.txt
  lat_file: lat.txt
  expt_dur: {service_expt_dur}
  rps: {rps}

taskset-service:
  set: false
  cpuid: 2

perf:
  collect: false
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



trace_path = [10,100,200,300,450,500,600,700,800,900,1000]
function_name="aes-nodejs-700000-707000"
yaml_path = "/users/Lakshman/vSwarm/tools/load-generator/yamls/aes-nodejs/kn-aes-nodejs-700000-707000.yaml"
grep_string = "/app/server"
predeployment_command = ""
load_expt_dur = 4
load_warmup_dur = 1
service_expt_dur = load_expt_dur + load_warmup_dur
rps=0.2
stat_expt_dur = load_expt_dur - 1
stat_warmup_dur = load_warmup_dur
stat_interval_print_ms = 500

for i in range(len(trace_path)):

    file_name=f"config-{function_name}-{trace_path[i]}.yaml"
    output_files_path = f"/users/Lakshman/vSwarm/tools/load-generator/expt/{function_name}-{trace_path[i]}"
    log_files_path = f"/users/Lakshman/vSwarm/tools/load-generator/expt/{function_name}-{trace_path[i]}" 

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

