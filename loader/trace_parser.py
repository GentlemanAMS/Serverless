import csv
import json
import sys

def read_durations_csv(directory_name):

    file_path = directory_name + '/durations.csv'
    functions = {}
    
    with open(file_path, 'r') as csv_file:
    
        csv_reader = csv.reader(csv_file) # Create a CSV reader object
    
        first_row = next(csv_reader)
        if len(first_row) != 14:
            print(f"Illegal header: {directory_name}/durations.csv")
            sys.exit(1)
        hashowner_index = first_row.index('HashOwner')
        hashapp_index = first_row.index('HashApp')
        hashfunction_index = first_row.index('HashFunction')
        average_index = first_row.index('Average')
        count_index = first_row.index('Count')
        minimum_index = first_row.index('Minimum')
        maximum_index = first_row.index('Maximum')
        percentile0_index = first_row.index('percentile_Average_0')
        percentile1_index = first_row.index('percentile_Average_1')
        percentile25_index = first_row.index('percentile_Average_25')
        percentile50_index = first_row.index('percentile_Average_50')
        percentile75_index = first_row.index('percentile_Average_75')
        percentile99_index = first_row.index('percentile_Average_99')
        percentile100_index = first_row.index('percentile_Average_100')

        for row in csv_reader:
            if len(row) != 14:
                print(f"Illegal entry: {directory_name}/durations.csv")
                sys.exit(1)
            function_name = row[hashowner_index] + row[hashapp_index] + row[hashfunction_index] # HashOwner + HashApp + HashFunction
            functions[function_name] = {}
            functions[function_name]['name'] = function_name            
            functions[function_name]['duration-avg'] = float(row[average_index])
            functions[function_name]['duration-cnt'] = float(row[count_index])
            functions[function_name]['duration-min'] = float(row[minimum_index])
            functions[function_name]['duration-max'] = float(row[maximum_index])
            functions[function_name]['duration-0%tile'] = float(row[percentile0_index])
            functions[function_name]['duration-1%tile'] = float(row[percentile1_index])
            functions[function_name]['duration-25%tile'] = float(row[percentile25_index])
            functions[function_name]['duration-50%tile'] = float(row[percentile50_index])
            functions[function_name]['duration-75%tile'] = float(row[percentile75_index])
            functions[function_name]['duration-99%tile'] = float(row[percentile99_index])
            functions[function_name]['duration-100%tile'] = float(row[percentile100_index])

    return functions




def read_memory_csv(directory_name):

    file_path = directory_name + '/memory.csv'
    functions = {}
    
    with open(file_path, 'r') as csv_file:

        csv_reader = csv.reader(csv_file) # Create a CSV reader object
        
        first_row = next(csv_reader)
        if len(first_row) != 13:
            print(f"Illegal header: {directory_name}/memory.csv")
            sys.exit(1)
        hashowner_index = first_row.index('HashOwner')
        hashapp_index = first_row.index('HashApp')
        hashfunction_index = first_row.index('HashFunction')
        count_index = first_row.index('SampleCount')
        average_index = first_row.index('AverageAllocatedMb')
        percentile1_index = first_row.index('AverageAllocatedMb_pct1')
        percentile5_index = first_row.index('AverageAllocatedMb_pct5')
        percentile25_index = first_row.index('AverageAllocatedMb_pct25')
        percentile50_index = first_row.index('AverageAllocatedMb_pct50')
        percentile75_index = first_row.index('AverageAllocatedMb_pct75')
        percentile95_index = first_row.index('AverageAllocatedMb_pct95')
        percentile99_index = first_row.index('AverageAllocatedMb_pct99')
        percentile100_index = first_row.index('AverageAllocatedMb_pct100')        

        for row in csv_reader:
            if len(row) != 13:
                print(f"Illegal entry: {directory_name}/memory.csv")
                sys.exit(1)
            function_name = row[hashowner_index] + row[hashapp_index] + row[hashfunction_index] # HashOwner + HashApp + HashFunction
            functions[function_name] = {}
            functions[function_name]['name'] = function_name            
            functions[function_name]['memory-cnt'] = float(row[count_index])
            functions[function_name]['memory-avg'] = float(row[average_index])
            functions[function_name]['memory-1%tile'] = float(row[percentile1_index])
            functions[function_name]['memory-5%tile'] = float(row[percentile5_index])
            functions[function_name]['memory-25%tile'] = float(row[percentile25_index])
            functions[function_name]['memory-50%tile'] = float(row[percentile50_index])
            functions[function_name]['memory-75%tile'] = float(row[percentile75_index])
            functions[function_name]['memory-95%tile'] = float(row[percentile95_index])
            functions[function_name]['memory-99%tile'] = float(row[percentile99_index])
            functions[function_name]['memory-100%tile'] = float(row[percentile100_index])
    
    return functions




def read_invocations_csv(directory_name):

    file_path = directory_name + '/invocations.csv'
    functions = {}

    with open(file_path, 'r') as csv_file:

        csv_reader = csv.reader(csv_file) # Create a CSV reader object

        first_row = next(csv_reader)
        if len(first_row) <= 4:
            print(f"Illegal header: {directory_name}/invocations.csv")
            sys.exit(1)
        hashowner_index = first_row.index('HashOwner')
        hashapp_index = first_row.index('HashApp')
        hashfunction_index = first_row.index('HashFunction')
        trigger_index = first_row.index('Trigger')

        for row in csv_reader:
            if len(row) <= 4:
                print(f"Illegal entry: {directory_name}/invocations.csv")
                sys.exit(1)
            function_name = row[hashowner_index] + row[hashapp_index] + row[hashfunction_index] # HashOwner + HashApp + HashFunction
            functions[function_name] = {}
            functions[function_name]['name'] = function_name            
            functions[function_name]['trigger'] = row[trigger_index]
            invocation = row[4:]
            invocation = [int(i) for i in invocation]
            functions[function_name]['num-of-invocations-per'] = invocation

    return functions

def load_trace(directory_name):
    durations_info = read_durations_csv(directory_name)
    memory_info = read_memory_csv(directory_name)
    invocations_info = read_invocations_csv(directory_name)
    functions = {}
    for function_name in durations_info.keys():
        functions[function_name] = durations_info[function_name].copy()
        functions[function_name].update(memory_info[function_name])
        functions[function_name].update(invocations_info[function_name])
    return functions




