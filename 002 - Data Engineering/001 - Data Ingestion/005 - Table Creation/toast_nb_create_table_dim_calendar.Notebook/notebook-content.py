# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "19d0a156-0ba5-48d9-ad24-2d55e56083dc",
# META       "default_lakehouse_name": "toast_lh_workfront_cleaned",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "19d0a156-0ba5-48d9-ad24-2d55e56083dc"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, date_format, year, month, dayofmonth, weekofyear,
    dayofweek, lit, when, explode, sequence, to_date
)

import logging

# === STEP 0: Initialize Spark session and logger ===
spark = SparkSession.builder.getOrCreate()
logger = logging.getLogger(__name__)

# === STEP 1: CONFIGURATION ===
# - Define workspace and lakehouse IDs.
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
lakehouse_id_cleaned = "19d0a156-0ba5-48d9-ad24-2d55e56083dc"

# === STEP 2: Define cleaned lakehouse input and output paths ===
input_table_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_cleaned}/Tables/dbo/workfront_hour"
output_calendar_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_cleaned}/Tables/dbo/dim_calendar"

# === STEP 3: Read min and max date from cleaned workfront_hour ===
try:
    df_hours = spark.read.format("delta").load(input_table_path)
    date_bounds = df_hours.selectExpr("MIN(lastUpdateDate) AS min_date", "MAX(lastUpdateDate) AS max_date").collect()[0]
    min_date = date_bounds["min_date"]
    max_date = date_bounds["max_date"]
except Exception as e:
    raise ValueError("Unable to retrieve date range from cleaned.workfront_hour.") from e

if min_date is None or max_date is None:
    raise ValueError("No lastUpdateDate values found in cleaned.workfront_hour.")

logger.info(f"Generating calendar from {min_date} to {max_date}.")

# === STEP 4: Generate date range as one row per day ===
date_df = spark.sql(f"""
    SELECT explode(sequence(to_date('{min_date}'), to_date('{max_date}'), interval 1 day)) as date
""")

# === STEP 5: Build enriched calendar DataFrame with useful attributes ===
calendar_df = (
    date_df
    .withColumn("index", month("date"))
    .withColumn("day_nm", date_format("date", "E"))
    .withColumn("day", dayofmonth("date"))
    .withColumn("month", date_format("date", "MMM"))
    .withColumn("month_long", date_format("date", "MMMM"))
    .withColumn("week", weekofyear("date"))
    .withColumn("year", year("date"))
    .withColumn("day_number", dayofweek("date"))  # Sunday = 1
    .withColumn("is_weekday", when(dayofweek("date").isin([1, 7]), lit(0)).otherwise(lit(1)))
    .withColumn("date_sk", date_format("date", "yyyyMMdd").cast("int"))
)

# === STEP 6: Save enriched calendar to cleaned Lakehouse via full abfss path ===
calendar_df.write.format("delta").mode("overwrite").save(output_calendar_path)

logger.info(f"dim_calendar saved to: {output_calendar_path}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
