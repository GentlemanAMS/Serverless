import re
from collections import defaultdict
import numpy as np

def parse_files_get_cpi(filenames, function_names):
    function_cpi = defaultdict(list)

    function_pattern = re.compile(r'|'.join(map(re.escape, function_names)))

    for filename in filenames:
        with open(filename, 'r') as file:
            current_function = None

            for line in file:
                line = line.strip()

                # Check if the line matches any of the function names
                if function_pattern.match(line):
                    current_function = line

                # Match lines starting with 'cpi' and capture the values
                elif current_function and line.startswith("lat-p75"):
                    # Extracting the cpi values
                    cpi_values = line.split()[1:]  # Skip the 'cpi' label and take the values
                    # Replace 'N/A' with 0 and convert to float
                    cpi_values = [float(value) if value != 'N/A' else 0.0 for value in cpi_values]
                    function_cpi[current_function].append(cpi_values)

    return function_cpi

# Example usage
filenames = ['results-1/results.txt', 'results-2/results.txt', 'results-3/results.txt', 'results-4/results.txt']  # Replace with your actual file names
function_names = [
    "aes-nodejs-100000-101000",
    "aes-nodejs-700000-707000",
    "aes-go-1000000-1010000",
    "aes-python-500-505",
    "aes-python-45000-45450",
    "aes-python-200000-202000",
    "fibonacci-go-70000-70700",
    "fibonacci-go-200000-202000",
    "fibonacci-go-450000-454500",
    "fibonacci-python-20000-20200",
    "fibonacci-python-200000-202000",
    "gptj-python",
    "image-rotate-go-3",
    "image-rotate-go-6",
    "image-rotate-go-14",
    "image-rotate-python-7",
    "image-rotate-python-11",
    "image-rotate-python-17",
    "rnn-serving-python-20-20",
    "rnn-serving-python-100-101",
    "rnn-serving-python-1000-1010",
    "video-analytics-standalone-python-10",
    "video-analytics-standalone-python-30",
    "video-analytics-standalone-python-70",
    "video-processing-python-70",
    "video-processing-python-450",
    "video-processing-python-1500"
]

cpi_data = parse_files_get_cpi(filenames, function_names)

for function, cpi_values in cpi_data.items():
    print(function)
    header = "".join([f"{folder:<15}" for folder in ["10", "200", "300", "400"]])
    print(header)
    for each_run in cpi_values:
        row = ""
        for value in each_run:
            row += f"{value:<15}"
        print(row)
    print("\n")

print("\n\n\n")


for function, cpi_values in cpi_data.items():
    a = [[],[],[],[]]
    for each_run in cpi_values:
        if each_run[0] != 0.0: a[0].append(each_run[0])
        if each_run[1] != 0.0: a[1].append(each_run[1])
        if each_run[2] != 0.0: a[2].append(each_run[2])
        if each_run[3] != 0.0: a[3].append(each_run[3])
    cpi_data[function] = a    
# print(cpi_data)


for function, cpi_values in cpi_data.items():
    row = ""
    row += f"{function:<70}"
    row += f"{np.mean(cpi_values[0]):<15.5f}"
    row += f"{np.mean(cpi_values[1]):<15.5f}"
    row += f"{np.mean(cpi_values[2]):<15.5f}"
    row += f"{np.mean(cpi_values[3]):<15.5f}"
    row += f"{np.std(cpi_values[0]):<15.5f}"
    row += f"{np.std(cpi_values[1]):<15.5f}"
    row += f"{np.std(cpi_values[2]):<15.5f}"
    row += f"{np.std(cpi_values[3]):<15.5f}"
    print(row)

print("\n\n\n")


for function, cpi_values in cpi_data.items():
    row = ""
    # row += f"{function},"
    row += f"{np.mean(cpi_values[0])},"
    row += f"{np.mean(cpi_values[1])},"
    row += f"{np.mean(cpi_values[2])},"
    row += f"{np.mean(cpi_values[3])}"
    print(row)

print("\n\n\n")
