import json
from collections import OrderedDict
import numpy as np
import scipy.optimize as sp

# def get_proxy_function(function):
#     endpoint = function['name'][:10] + '.10.21.01.1'
#     proxy = function['name'][:10]
#     return proxy, endpoint



def read_proxy_function_json(directory_name):
    json_file_path = directory_name + '/proxy_functions.json'
    with open(json_file_path, 'r') as json_file:
        proxy_functions = json.load(json_file, object_pairs_hook=OrderedDict)   
    return proxy_functions

# TODO: Remove proxy functions that are not deployed. Also attach endpoints to this dictionary
# NOTE: its necessary that user does not deploy functions that are chained or pipelined
# i.e., invoking one function must not invoke other functions. Else it will damage the trace
def attach_endpoints_to_proxy_functions(proxy_functions):
    # TODO: Writing a temporary setup. Needs to be changed
    for function_name in proxy_functions:
        proxy_functions[function_name]['endpoint'] = function_name + '.10.21.0.1'
    return proxy_functions


# NOTE: Better Error mechanisms can be considered to improve the correlation
# Currently only the 75%tile memory and duration are considered. 
def get_error(trace_memory, trace_duration, proxy_memory, proxy_duration):
    diff_memory = (trace_memory - proxy_memory) / trace_memory
    diff_duration = (trace_duration - proxy_duration) / proxy_duration
    error = (diff_memory) ** 2 +  (diff_duration) ** 2
    return error



def correlate_trace_function_with_proxy_function(trace_functions, proxy_functions):
    
    trace_memory = []
    trace_duration = []
    for function_name in trace_functions:
        trace_memory.append(trace_functions[function_name]['memory'])
        trace_duration.append(trace_functions[function_name]['duration'])
        trace_functions[function_name]['index'] = len(trace_memory) - 1

    proxy_memory = []
    proxy_duration = []
    for function_name in proxy_functions:
        proxy_memory.append(proxy_functions[function_name]['memory'])
        proxy_duration.append(proxy_functions[function_name]['duration'])
        proxy_functions[function_name]['index'] = len(proxy_memory) - 1

    m, n = len(trace_functions.keys()), len(proxy_functions.keys())
    error_matrix = np.empty((m, n))

    # This utilized Jonker-Volgenant algorithm for Linear Sum assignment - scipy package
    # to calculate the best possible assignment for the trace functions 
    # Time complexity : O(n^3) where n is the largest of number of rows/columns
    for i in range(m):
        for j in range(n):
            error_matrix[i, j] = get_error(trace_memory[i], trace_duration[i], proxy_memory[j], proxy_duration[j])

    row_indices, col_indices = sp.linear_sum_assignment(error_matrix)
    assignments = list(zip(row_indices, col_indices))

    for assignment in assignments:
        row_index = assignment[0]
        col_index = assignment[1]
        trace = None
        proxy = None
        for trace_function_name in trace_functions:
            if row_index == trace_functions[trace_function_name]['index']:
                trace = trace_function_name
                break
        for proxy_function_name in proxy_functions:
            if col_index == proxy_functions[proxy_function_name]['index']:
                proxy = proxy_function_name
                break        
        trace_functions[trace]['proxy'] = proxy

    return trace_functions



def get_proxy_function(functions):
    
    # Parse through the trace functions to get 75% duration and 75% memory
    # TODO: Ask whether this criteria is sufficient or not?
    trace_functions = OrderedDict()
    for function_name in functions:
        trace_functions[function_name] = {}
        trace_functions[function_name]['duration'] = functions[function_name]['duration-75%tile']
        trace_functions[function_name]['memory'] = functions[function_name]['memory-75%tile']
    
    proxy_functions = read_proxy_function_json('.')
    proxy_functions = attach_endpoints_to_proxy_functions(proxy_functions)

    trace_functions = correlate_trace_function_with_proxy_function(trace_functions, proxy_functions)
    for function_name in trace_functions:
        functions[function_name]['proxy'] = trace_functions[function_name]['proxy']
        functions[function_name]['endpoint'] = proxy_functions[trace_functions[function_name]['proxy']]['endpoint']

    return functions