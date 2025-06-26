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
from pyspark.sql.types import StringType, BooleanType

# Configuration
API_KEY = "al7s4u94ggluu08vnh7atni3p5sagebm"
BASE_URL = "https://teladochealth.my.workfront.com/attask/api/v19.0/user/search"
FIELDS = "ID,name,username,manager:name,isActive"
LIMIT = 2000  # Max rows per request
RETRY_DELAY = 1  # Seconds to wait before retrying on failure
MAX_RETRIES = 3  # Maximum number of retries per request

def fetch_user_data(first=0):
    """Fetch user data with pagination."""
    all_data = []
    while True:
        # Construct query parameters
        params = {
            "apiKey": API_KEY,
            "method": "GET",
            "fields": FIELDS,
            "$$FIRST": first,
            "$$LIMIT": LIMIT,
            "ID_Sort": "asc"
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
                print(f"Fetched {len(data['data'])} records, total {len(all_data)}")
                
                # Check if more data exists
                if len(data["data"]) < LIMIT:
                    return all_data
                
                # Update first for next batch
                first += LIMIT
                break  # Exit retry loop on success
                
            except requests.RequestException as e:
                print(f"Error fetching data, attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    sleep(RETRY_DELAY)
                else:
                    print(f"Max retries reached at first={first}")
                    return all_data
        
        # Small delay to avoid overwhelming the API
        sleep(0.1)

def main():
    """Fetch user data, process it, and save as a table."""
    # Fetch all user data
    all_records = fetch_user_data()
    
    # Initialize df as an empty DataFrame
    df = pd.DataFrame()
    
    # Process data if records exist
    if all_records:
        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        print(f"Total records fetched: {len(df)}")
        
        # Expand manager column (handle cases where manager is None)
        df['manager_id'] = df['manager'].apply(lambda x: x['ID'] if isinstance(x, dict) and 'ID' in x else None)
        df['manager_name'] = df['manager'].apply(lambda x: x['name'] if isinstance(x, dict) and 'name' in x else None)
        df['manager_objCode'] = df['manager'].apply(lambda x: x['objCode'] if isinstance(x, dict) and 'objCode' in x else None)
        
        # Drop the original manager column
        df = df.drop(columns=['manager'])
        
        # Rename columns to match M code
        df = df.rename(columns={
            'ID': 'user_id',
            'name': 'user_nm',
            'username': 'user_username',
            'manager_id': 'manager_id',
            'manager_name': 'manager_nm',
            'manager_objCode': 'manager_objCode',
            'isActive': 'isActive'
        })
        
        # Remove unnecessary columns
        df = df.drop(columns=['manager_objCode'], errors='ignore')
        
        # Set data types to match M code
        df = df.astype({
            'user_id': 'string',
            'user_nm': 'string',
            'user_username': 'string',
            'manager_id': 'string',
            'manager_nm': 'string',
            'isActive': 'bool'
        }, errors='ignore')
        
        # Display first few rows
        display(df.head())
        
        # Save to Fabric Lakehouse as Parquet
        lakehouse_path = "https://app.powerbi.com/groups/b08d383a-b8cc-4b8e-b189-d9d696a01977/lakehouses/a15ff84e-a191-4d61-ab82-417f17c97822?experience=power-bi"
        df.to_parquet(lakehouse_path, index=False)
        print(f"Data saved to {lakehouse_path}")
        
        # Register as a table named 'user' in the Lakehouse
        spark_df = spark.createDataFrame(df)
        spark_df.write.mode("overwrite").saveAsTable("user")
        print("Table 'user' created in the Lakehouse")
        
    else:
        print("No data retrieved from the API.")
    
    return df

# Execute in Fabric notebook
if __name__ == "__main__":
    df = main()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
