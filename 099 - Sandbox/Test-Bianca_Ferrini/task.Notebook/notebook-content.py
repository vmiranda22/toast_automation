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

def fetch_all_tasks(api_key, base_url):
    """
    Fetch all tasks from Workfront API with all fields, handling pagination (1000 rows per request).
    
    Args:
        api_key (str): Workfront API key
        base_url (str): Base URL for the API endpoint
    
    Returns:
        list: List of all task data with all fields
    """
    all_tasks = []
    first = 0
    limit = 1000
    headers = {"apiKey": api_key}
    
    while True:
        # Construct the URL with pagination parameters and name_Mod filter, omitting fields to get all
        url = f"{base_url}?method=GET&name_Mod=cicontains&$$FIRST={first}&$$LIMIT={limit}"
        
        try:
            # Make the API request
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error for bad status codes
            
            # Parse the JSON response
            data = response.json()
            tasks = data.get("data", [])
            
            # If no more tasks, break the loop
            if not tasks:
                break
                
            # Add tasks to the result list
            all_tasks.extend(tasks)
            
            # Update the starting index for the next request
            first += limit
            
            # Optional: Add a small delay to avoid hitting rate limits
            time.sleep(0.1)
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break
            
    return all_tasks

# Configuration
api_key = "al7s4u94ggluu08vnh7atni3p5sagebm"
base_url = "https://teladochealth.my.workfront.com/attask/api/v19.0/task/search"
output_file = "workfront_tasks.json"

# Fetch all tasks
tasks = fetch_all_tasks(api_key, base_url)

# Print the total number of tasks fetched
print(f"Total tasks fetched: {len(tasks)}")

# Optionally, save the results to a JSON file
import json
with open(output_file, "w") as f:
    json.dump(tasks, f, indent=2)

# Example: Print the first task with all fields (limited to first task for brevity)
if tasks:
    print("Sample task (first task with all fields):")
    print(json.dumps(tasks[0], indent=2))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
