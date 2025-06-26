# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "a852188b-a853-4fd2-b6fb-541fa5469293",
# META       "default_lakehouse_name": "toast_lh_salesforce_lcrm_raw",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "a852188b-a853-4fd2-b6fb-541fa5469293"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

"""
This PySpark notebook performs an incremental merge of Salesforce `{object_name}` data
into a raw merged Delta table that holds the latest known version of each record by Id.
It also logs the merge execution time into a cursor table to monitor whether objects
are being refreshed hourly.

Parameters:
- object_name: Name of the Salesforce object (e.g., 'account', 'contact', 'member_group').
- recent_raw_path: ABFSS path to the raw 7-day Delta table for the object.
- merged_raw_path: ABFSS path to the raw merged Delta table that stores latest records.

Behavior:
1. Reads recent data from the raw 7-day table.
2. Deduplicates the recent data by Id, keeping the most recent record based on SystemModstamp.
3. Computes a SHA-256 row hash using all fields except 'Id'.
4. If the merged table doesn't exist or lacks `row_hash`, it is initialized from scratch.
5. Otherwise, only newer and changed records are merged into the raw merged table.
6. If records were merged, logs the object name and current UTC timestamp to a cursor table.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import sha2, concat_ws, col, row_number, max as spark_max
from pyspark.sql.window import Window
from delta.tables import DeltaTable
from datetime import datetime
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# -----------------------------
# Parameters
object_name = "subscription"

base_path = "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/a852188b-a853-4fd2-b6fb-541fa5469293/Tables/dbo"
recent_raw_path = f"{base_path}/salesforce_lcrm_{object_name}_raw_recent"
merged_raw_path = f"{base_path}/salesforce_lcrm_{object_name}_raw_full"
cursor_table_path = f"{base_path}/salesforce_ingestion_cursor"
# -----------------------------

spark = SparkSession.builder.getOrCreate()

# Step 1: Load recent 7-day raw data
df_recent = spark.read.format("delta").load(recent_raw_path)

# Step 2: Compute row_hash from all fields except 'Id'
excluded_cols = {"Id"}
hash_cols = [c for c in df_recent.columns if c not in excluded_cols]

df_hashed = df_recent.withColumn(
    "row_hash", sha2(concat_ws("||", *[col(c).cast("string") for c in hash_cols]), 256)
)

# Step 3: Deduplicate by most recent SystemModstamp per Id
window = Window.partitionBy("Id").orderBy(col("SystemModstamp").desc())
df_dedup = df_hashed.withColumn("rn", row_number().over(window)).filter("rn = 1").drop("rn")

# Step 4: Merge into or create raw full table
if not DeltaTable.isDeltaTable(spark, merged_raw_path):
    df_dedup.write \
        .format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save(merged_raw_path)
    print(f"Created raw merged table at: {merged_raw_path}")
    merge_count = df_dedup.count()
else:
    delta_table = DeltaTable.forPath(spark, merged_raw_path)
    existing_cols = delta_table.toDF().columns

    if "row_hash" not in existing_cols:
        print("Merged table exists but lacks 'row_hash'. Overwriting with deduplicated data.")
        df_dedup.write \
            .format("delta") \
            .option("overwriteSchema", "true") \
            .mode("overwrite") \
            .save(merged_raw_path)
        print(f"Overwritten merged raw table at: {merged_raw_path}")
        merge_count = df_dedup.count()
    else:
        df_existing = delta_table.toDF().select("Id", "row_hash", "SystemModstamp") \
            .withColumnRenamed("row_hash", "existing_hash") \
            .withColumnRenamed("SystemModstamp", "existing_SystemModstamp")

        df_to_merge = df_dedup.join(df_existing, on="Id", how="left_outer") \
            .filter(
                (col("row_hash") != col("existing_hash")) | col("existing_hash").isNull()
            ) \
            .drop("existing_hash", "existing_SystemModstamp")

        merge_count = df_to_merge.count()

        if merge_count > 0:
            delta_table.alias("target").merge(
                source=df_to_merge.alias("source"),
                condition="target.Id = source.Id"
            ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
            print(f"Merged {merge_count} rows into raw merged table.")
        else:
            print("No new or changed records to merge.")

# Step 5: Log successful merge into the cursor table (only if rows were merged)
if merge_count > 0:
    log_schema = StructType([
        StructField("object_name", StringType(), False),
        StructField("updated_at", TimestampType(), False)
    ])

    cursor_row = spark.createDataFrame([{
        "object_name": object_name,
        "updated_at": datetime.utcnow()
    }], schema=log_schema)

    if DeltaTable.isDeltaTable(spark, cursor_table_path):
        cursor_table = DeltaTable.forPath(spark, cursor_table_path)
        cursor_table.alias("target").merge(
            source=cursor_row.alias("source"),
            condition="target.object_name = source.object_name"
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        print(f"Logged update to cursor table for '{object_name}'.")
    else:
        cursor_row.write \
            .format("delta") \
            .mode("overwrite") \
            .save(cursor_table_path)
        print(f"Created cursor table and logged update for '{object_name}'.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
