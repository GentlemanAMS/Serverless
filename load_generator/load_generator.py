import trace_parser as tp
import proxy_function as pf
import numpy as np
import random
import sys
import json

# TODO: add shiftIAT to generate_iat_per_granularity

ONE_SECOND_TO_MICROSECONDS = 1000000
ONE_MINUTE_TO_SECONDS = 60

def generate_random_fp(distribution):

    if distribution == 'exponential':
        lambda_parameter = 0.5
        # NOTE:
        # This is causing problems when normalization_factor += iat, and normalizing based on normalization_factor
        # When the number_of_invocations = 1, then normalization_factor = iat, and it is always normalized to 1
        # return abs(np.random.exponential(scale=1/lambda_parameter))
        random_numbers = abs(np.random.exponential(scale=1/lambda_parameter, size=1000))
        normalized_numbers = (random_numbers - np.min(random_numbers)) / (np.max(random_numbers) - np.min(random_numbers))
        return normalized_numbers[0]
    
    
    elif distribution == 'uniform':
        return random.uniform(0.0, 1.0)



def generate_iat_per_granularity (number_of_invocations, iat_distribution, minute_granularity):
    
    if number_of_invocations == 0: return []
    
    iat_result = []
    normalization_factor = 0

    for i in range(number_of_invocations):

        if iat_distribution == 'exponential':
            iat = generate_random_fp('exponential')
        elif iat_distribution == 'uniform':
            iat = generate_random_fp('uniform')
        elif iat_distribution == 'equidistant':
            equal_distance = ONE_SECOND_TO_MICROSECONDS / number_of_invocations
            if minute_granularity: equal_distance = equal_distance / ONE_MINUTE_TO_SECONDS
            iat = equal_distance
        else:
            print(f"Invaild IAT distribution: {iat_distribution}")
            sys.exit(1)

        iat_result.append(iat)
        normalization_factor += 1

    # Normalize IAT
    iat_result = [iat / normalization_factor for iat in iat_result]
    iat_result = [iat * ONE_SECOND_TO_MICROSECONDS for iat in iat_result]
    if minute_granularity: iat_result = [iat * ONE_MINUTE_TO_SECONDS for iat in iat_result]
    iat_result = [int(iat) for iat in iat_result]

    return iat_result


def generate_iat (invocations_per_minute, iat_distribution, minute_granularity):
    iat = []
    for number_of_invocations in invocations_per_minute:
        iat.append(generate_iat_per_granularity(number_of_invocations, iat_distribution, minute_granularity))
    return iat


def load_trace(directory_name, iat_distribution, minute_granularity):
    functions = tp.load_trace(directory_name)
    for function_name in functions:
        functions[function_name]['invocations'] = generate_iat(functions[function_name]['num-of-invocations-per'], iat_distribution, minute_granularity)
        # proxy_function, proxy_function_endpoint = pf.get_proxy_function(functions[function_name])
        # functions[function_name]['proxy'] = proxy_function
        # functions[function_name]['endpoint'] = proxy_function_endpoint
    functions = pf.get_proxy_function(functions)
    return functions




def timestamp_generation(functions, duration):
    load = []

    for minute in range(duration):
        invocations_dict = {}
        for function_name in functions:
            for iat in functions[function_name]['invocations'][minute]:
                invocations_dict[iat] = functions[function_name]['endpoint']
        invocation_timestamp = list(invocations_dict.keys())
        invocation_timestamp.sort()
        invocation_endpoint = []
        for timestamp in invocation_timestamp:
            invocation_endpoint.append(invocations_dict[timestamp]) 
        load.append({"timestamp":invocation_timestamp,"endpoint":invocation_endpoint})

    return load


def load_generator():

    file_path = 'config.json'
    with open(file_path, 'r') as json_file:
        config = json.load(json_file)

    directory_name = config["TracePath"]
    iat_distribution = config["IATDistribution"]
    minute_granularity = config["MinuteGranularity"]
    duration = config["ExperimentDuration"] + config["WarmupDuration"]
    output_json_file_path = config["OutputPathPrefix"] + '/load.json'

    functions = load_trace(directory_name, iat_distribution, minute_granularity)
    load = timestamp_generation(functions, duration)   
    # json_data = json.dumps(load, indent=2)
    # print(json_data)
    with open(output_json_file_path, 'w') as json_file:
        json.dump(load, json_file, indent=2)


load_generator()





