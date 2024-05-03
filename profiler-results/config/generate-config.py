import json

# List of x values
x_values = [300, 400, 500, 600, 700, 800, 900]

# List to store details for each YAML file
yaml_details = []

# Generate YAML files for each combination of x and y values
for x in x_values:
    y = int(1.01 * x)
    yaml_location = f"./yamls/video-analytics-standalone/kn-video-analytics-standalone-python-{x}.yaml"
    details = {
        "yaml-location": yaml_location,
        "predeployment-commands": ["kubectl apply -f ./yamls/video-analytics-standalone/video-analytics-standalone-database.yaml"],
        "postdeployment-commands": []
    }
    yaml_details.append(details)

# Write the details to a JSON file
output_filename = "config.json"
with open(output_filename, "w") as f:
    json.dump(yaml_details, f, indent=4)
print(f"Created {output_filename}")