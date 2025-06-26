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
import json
import pandas as pd
from time import sleep

# Configuration
API_KEY = "al7s4u94ggluu08vnh7atni3p5sagebm"
BASE_URL = "https://teladochealth.my.workfront.com/attask/api/v19.0/HOUR/search"
PROJECT_IDS = [
    "6631759700359935229b219fe6871de6",
    "6750ce620019a9ea7e9bc8f9943b76c3",
    "677d615400218833583a0848c6cef311"
]
FIELDS = "hours,task:name,project:name,entryDate,owner:name,status"
LIMIT = 2000  # Max rows per request
RETRY_DELAY = 1  # Seconds to wait before retrying on failure
MAX_RETRIES = 3  # Maximum number of retries per request

def fetch_data_for_project(project_id, first=0):
    """Fetch data for a single project with pagination."""
    all_data = []
    while True:
        # Construct query parameters
        params = {
            "apiKey": API_KEY,
            "method": "GET",
            "projectID": project_id,
            "fields": FIELDS,
            "$$FIRST": first,
            "$$LIMIT": LIMIT
        }
        
        # Make API request with retries
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(BASE_URL, params=params)
                response.raise_for_status()  # Raise exception for bad status codes
                data = response.json()
                
                # Check if data key exists and has records
                if "data" not in data or not data["data"]:
                    return all_data
                
                # Append new records
                all_data.extend(data["data"])
                print(f"Project {project_id}: Fetched {len(data['data'])} records, total {len(all_data)}")
                
                # Check if more data exists
                if len(data["data"]) < LIMIT:
                    return all_data
                
                # Update first for next batch
                first += LIMIT
                break  # Exit retry loop on success
                
            except requests.RequestException as e:
                print(f"Error fetching data for project {project_id}, attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    sleep(RETRY_DELAY)
                else:
                    print(f"Max retries reached for project {project_id} at first={first}")
                    return all_data
        
        # Small delay to avoid overwhelming the API
        sleep(0.1)

def main():
    """Fetch data for all projects and combine results."""
    all_records = []
    
    # Fetch data for each project
    for project_id in PROJECT_IDS:
        print(f"Starting data fetch for project {project_id}")
        project_data = fetch_data_for_project(project_id)
        all_records.extend(project_data)
        print(f"Completed fetching {len(project_data)} records for project {project_id}")
    
    # Initialize df as an empty DataFrame
    df = pd.DataFrame()
    
    # Convert to DataFrame if records exist
    if all_records:
        df = pd.DataFrame(all_records)
        print(f"Total records fetched: {len(df)}")
        
        # Rename fields to avoid issues with colons
        df = df.rename(columns={
            "task:name": "task_name",
            "project:name": "project_name",
            "owner:name": "owner_name"
        })
        
        # Display first few rows
        display(df.head())
        
        # Save to Fabric Lakehouse as Parquet
        lakehouse_path = "https://app.powerbi.com/groups/b08d383a-b8cc-4b8e-b189-d9d696a01977/lakehouses/a15ff84e-a191-4d61-ab82-417f17c97822?experience=power-bi"
        df.to_parquet(lakehouse_path, index=False)
        print(f"Data saved to {lakehouse_path}")
        
        # Register as a table named 'hour' in the Lakehouse
        spark_df = spark.createDataFrame(df)
        spark_df.write.mode("overwrite").saveAsTable("hour")
        print("Table 'hour' created in the Lakehouse")
        
    else:
        print("No data retrieved from any project.")
    
    return df

# Execute in Fabric notebook
if __name__ == "__main__":
    df = main()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
