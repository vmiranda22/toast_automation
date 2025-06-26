# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "858ad52b-f017-4d74-9957-17175dd47103",
# META       "default_lakehouse_name": "toast_lh_workfront_raw",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "858ad52b-f017-4d74-9957-17175dd47103"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import requests
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Initialize Spark session
spark = SparkSession.builder.getOrCreate()

# API request details
url = "https://teladochealth.my.workfront.com/attask/api/v19.0/HOUR/search"
api_key = "al7s4u94ggluu08vnh7atni3p5sagebm"
project_id = "6631759700359935229b219fe6871de6"
fields = "hours,task:name,project:name,entryDate,owner:name,status,task:DE:Time Type"
limit = 2000
first = 0

# Initialize list to store all data
all_data = []

# Pagination loop
while True:
    # Set up query parameters
    params = {
        "apiKey": api_key,
        "method": "GET",
        "projectID": project_id,
        "fields": fields,
        "$$FIRST": first,
        "$$LIMIT": limit
    }

    # Make the API request
    response = requests.get(url, params=params)

    # Check if request was successful
    if response.status_code == 200:
        # Parse JSON response
        data = response.json()
        
        # Extract the 'data' list from the response
        hours_data = data.get('data', [])
        
        # Append to all_data
        all_data.extend(hours_data)
        
        # Check if we've fetched all records
        if len(hours_data) < limit:
            break
        
        # Increment for next page
        first += limit
    else:
        print(f"Error: {response.status_code} - {response.text}")
        break

# Check if data was retrieved
if not all_data:
    print("No data retrieved from API. Please check the API request or field names.")
else:
    # Convert to pandas DataFrame
    df_pandas = pd.DataFrame(all_data)

    # Rename columns for clarity
    df_pandas = df_pandas.rename(columns={
        'task:name': 'task_name',
        #'DE:Time Type': 'time_type',
        'project:name': 'project_name',
        'owner:name': 'owner_name'
    })

    # Validate presence of time_type
   #-- if 'time_type' not in df_pandas.columns:
      #--  print("Warning: 'time_type' field not found in API response. Available columns:", df_pandas.columns.tolist())

    # Convert pandas DataFrame to Spark DataFrame
    df_spark = spark.createDataFrame(df_pandas)

    # Define schema for the Delta table
    schema = StructType([
        StructField("hours", DoubleType(), True),
        StructField("task_name", StringType(), True),
        StructField("project_name", StringType(), True),
        StructField("entryDate", TimestampType(), True),
        StructField("owner_name", StringType(), True),
        StructField("status", StringType(), True)
       # StructField("time_type", StringType(), True)  # Custom field
    ])

    # Cast columns to appropriate types
    df_spark = df_spark.select(
        col("hours").cast("double").alias("hours"),
        col("task_name").cast("string").alias("task_name"),
        col("project_name").cast("string").alias("project_name"),
        col("entryDate").cast("timestamp").alias("entryDate"),
        col("owner_name").cast("string").alias("owner_name"),
        col("status").cast("string").alias("status")
       # col("time_type").cast("string").alias("time_type")
    )

    # Write to Delta table (overwrite mode to create/replace table)
    table_name = "silver_wf_hour"
    df_spark.write.format("delta").mode("overwrite").saveAsTable(table_name)

    # Display the first few rows of the table
    display(spark.table(table_name).limit(5))

    # Print table schema to verify
    spark.table(table_name).printSchema()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
