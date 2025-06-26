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

# Welcome to your new notebook
# Type here in the cell editor to add code!
import requests
import pandas as pd
from pyspark.sql import SparkSession
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
WORKFRONT_DOMAIN = "https://<your-domain>.my.workfront.com/attask/api/v19.0"
API_KEY = "<your-api-key>"  # Replace with your API key
OBJECTS = {
    "project": ["ID", "name", "status", "plannedStartDate", "plannedCompletionDate"],
    "hour": ["ID", "entryDate", "hours", "userID", "projectID"],
    "task": ["ID", "name", "projectID", "status", "plannedStartDate", "plannedCompletionDate"],
    "user": ["ID", "name", "emailAddr", "title"]
}
LIMIT = 2000
TABLE_PATH = "/lakehouse/default/Tables/"

# Initialize Spark session
spark = SparkSession.builder.appName("WorkfrontDataIngestion").getOrCreate()

def fetch_workfront_data(object_name, fields):
    """
    Fetch all data for a given Workfront object with pagination.
    Returns a list of all records.
    """
    all_data = []
    first = 0
    url = f"{WORKFRONT_DOMAIN}/{object_name}/search"
    params = {
        "apiKey": API_KEY,
        "method": "GET",
        "fields": ",".join(fields),
        "$$LIMIT": LIMIT,
        "$$FIRST": first
    }

    while True:
        try:
            params["$$FIRST"] = first
            logger.info(f"Fetching {object_name} data, offset: {first}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            
            if not data:
                logger.info(f"No more data for {object_name}. Total records fetched: {len(all_data)}")
                break
                
            all_data.extend(data)
            first += LIMIT
            logger.info(f"Fetched {len(data)} records for {object_name}. Total so far: {len(all_data)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {object_name} data at offset {first}: {str(e)}")
            raise

    return all_data

def create_delta_table(object_name, data, fields):
    """
    Convert data to DataFrame and save as Delta table in Lakehouse.
    """
    try:
        if not data:
            logger.warning(f"No data to save for {object_name}")
            return

        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Ensure only specified fields are included
        df = df[[col for col in fields if col in df.columns]]
        
        # Convert to Spark DataFrame
        spark_df = spark.createDataFrame(df)
        
        # Define table path
        table_path = f"{TABLE_PATH}{object_name}"
        
        # Save as Delta table (overwrite mode for simplicity)
        spark_df.write.mode("overwrite").format("delta").save(table_path)
        logger.info(f"Successfully saved {object_name} data to Delta table at {table_path}")
        
        # Register table in Lakehouse
        spark.sql(f"CREATE TABLE IF NOT EXISTS {object_name} USING DELTA LOCATION '{table_path}'")
        logger.info(f"Registered {object_name} as a table in Lakehouse")
        
    except Exception as e:
        logger.error(f"Error creating Delta table for {object_name}: {str(e)}")
        raise

def main():
    """
    Main function to fetch data for all objects and create Delta tables.
    """
    logger.info("Starting Workfront data ingestion")
    
    for object_name, fields in OBJECTS.items():
        try:
            logger.info(f"Processing object: {object_name}")
            # Fetch data
            data = fetch_workfront_data(object_name, fields)
            # Create Delta table
            create_delta_table(object_name, data, fields)
        except Exception as e:
            logger.error(f"Failed to process {object_name}: {str(e)}")
            continue
    
    logger.info("Workfront data ingestion completed")

if __name__ == "__main__":
    main()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
