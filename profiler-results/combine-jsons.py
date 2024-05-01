import os
import json
from pathlib import Path

def combine_config_json_files(input_dir, output_file):
    # Convert input directory to Path object for easier manipulation
    input_dir = Path(input_dir)

    # Initialize a list to store all the combined data
    combined_data = []

    # Loop through each file in the input directory
    for file_name in os.listdir(input_dir):
        # Check if the file is a JSON file
        if file_name.endswith('.json'):
            file_path = input_dir / file_name
            # Open and read the JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    # Load JSON data from file
                    data = json.load(file)
                    # Append the data to the combined list
                    combined_data.extend(data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {file_path}: {e}")

    # Write the combined data to the output JSON file
    with open(output_file, 'w', encoding='utf-8') as out_file:
        json.dump(combined_data, out_file, indent=4)




def combine_profile_json_files(input_dir, output_file):
    # Convert input directory to Path object for easier manipulation
    input_dir = Path(input_dir)

    # Initialize a list to store all the combined data
    combined_data = {}

    # Loop through each file in the input directory
    for file_name in os.listdir(input_dir):
        # Check if the file is a JSON file
        if file_name.endswith('.json'):
            file_path = input_dir / file_name
            # Open and read the JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    # Load JSON data from file
                    data = json.load(file)
                    # Append the data to the combined list
                    combined_data.update(data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {file_path}: {e}")

    # Write the combined data to the output JSON file
    with open(output_file, 'w', encoding='utf-8') as out_file:
        json.dump(combined_data, out_file, indent=4)

# Example usage
input_directory = 'config'
output_json_file = 'config.json'
combine_config_json_files(input_directory, output_json_file)

input_directory = 'profile'
output_json_file = 'profile.json'
combine_profile_json_files(input_directory, output_json_file)
