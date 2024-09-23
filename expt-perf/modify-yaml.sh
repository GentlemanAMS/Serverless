#!/bin/bash

# Check if the directory is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

directory=$1

# Check if the directory exists
if [ ! -d "$directory" ]; then
  echo "Directory not found!"
  exit 1
fi

# Find all YAML files in the directory and its subdirectories
find "$directory" -type f \( -name "kn-*.yaml" -o -name "kn-*.yml" \) | while read -r yaml_file; do
  echo "Processing file: $yaml_file"

  # Add nodeSelector under spec.template.spec before containers using yq
  yq eval '.spec.template.spec |= . + {"nodeSelector": {"node-role": "perfer"}}' "$yaml_file" -i

  echo "Added nodeSelector to $yaml_file"
done

echo "Processing complete."
