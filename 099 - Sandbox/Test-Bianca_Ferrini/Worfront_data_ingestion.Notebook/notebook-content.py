# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "a15ff84e-a191-4d61-ab82-417f17c97822",
# META       "default_lakehouse_name": "Workfront_data_ingestion_lh",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "a15ff84e-a191-4d61-ab82-417f17c97822"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import requests
import time

def fetch_all_projects(api_key, base_url):
    """
    Fetch all projects from Workfront API with all fields, handling pagination (2000 rows per request).
    
    Args:
        api_key (str): Workfront API key
        base_url (str): Base URL for the API endpoint
    
    Returns:
        list: List of all project data with all fields
    """
    all_projects = []
    first = 0
    limit = 2000
    headers = {"apiKey": api_key}
    
    while True:
        # Construct the URL with pagination parameters, omitting fields to get all
        url = f"{base_url}?method=GET&$$FIRST={first}&$$LIMIT={limit}"
        
        try:
            # Make the API request
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error for bad status codes
            
            # Parse the JSON response
            data = response.json()
            projects = data.get("data", [])
            
            # If no more projects, break the loop
            if not projects:
                break
                
            # Add projects to the result list
            all_projects.extend(projects)
            
            # Update the starting index for the next request
            first += limit
            
            # Optional: Add a small delay to avoid hitting rate limits
            time.sleep(0.1)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break
            
    return all_projects

# Configuration
api_key = "al7s4u94ggluu08vnh7atni3p5sagebm"
base_url = "https://teladochealth.my.workfront.com/attask/api/v19.0/proj/search"
output_file = "workfront_projects.json"

# Fetch all projects
projects = fetch_all_projects(api_key, base_url)

# Print the total number of projects fetched
print(f"Total projects fetched: {len(projects)}")

# Optionally, save the results to a JSON file
import json
with open(output_file, "w") as f:
    json.dump(projects, f, indent=2)

# Example: Print the first project with all fields (limited to first project for brevity)
if projects:
    print("Sample project (first project with all fields):")
    print(json.dumps(projects[0], indent=2))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
