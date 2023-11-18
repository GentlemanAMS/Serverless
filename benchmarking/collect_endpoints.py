import re
import subprocess
import json


# Do not invoke these services: USER INPUT
# User should change here only, do not touch the 'compulsory-avoid-services'
user_avoid_services = ["bert-python"]

# Compulsorily avoid these services: DO NOT TOUCH THIS
# These services are not to be invoked by the invoker because these functions
# are part of pipeline i.e., there exists functions that automatically invoke these.
# So invoker should not invoke them
compulsory_avoid_services = ["consumer"]
compulsory_avoid_services += ["recog", "decoder"]
compulsory_avoid_services += ["checkoutservice-shipping", "checkoutservice-prodcat", "checkoutservice-cart", "checkoutservice-currency", "checkoutservice-email", "checkoutservice-payment"]
compulsory_avoid_services += ["recommendationservice-prodcat"]
compulsory_avoid_services += ["hotel-app-search-geo", "hotel-app-search-rate"]

# Run the 'kn service list -A' command and capture the output
try:
    result = subprocess.run(['kn', 'service', 'list', '-A'], capture_output=True, text=True, check=True)
    output = result.stdout
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
    output = ""

# Define a regular expression pattern to match URLs
url_pattern = re.compile(r'http://(\S+)')

# Find all matches in the output
matches = re.findall(url_pattern, output)

# Remove "http://" prefix
matches = [match.replace("http://","") for match in matches]

#for each_url in matches:
#    print(f"{each_url.split('.')[0]}")
#print(f"{user_avoid_services}")
#print(f"{compulsory_avoid_services}")

# Remove these functions
matches = [url for url in matches if not url.split('.')[0] in compulsory_avoid_services]
matches = [url for url in matches if not url.split('.')[0] in user_avoid_services]

# Remove "http://" prefix and store in a list
url_list = [{'hostname': match} for match in matches]

# Print the functions that are getting invoked
print(f"Functions that are getting invoked")
for each_url in matches:
    print(f"{each_url}")

# Convert the list to JSON format
json_output = json.dumps(url_list, indent=3)

# Write the JSON output to endpoints.json
json_file = open('./endpoints.json', 'w')
json_file.write(json_output)
json_file.close()

print("JSON data written to endpoints.json")
