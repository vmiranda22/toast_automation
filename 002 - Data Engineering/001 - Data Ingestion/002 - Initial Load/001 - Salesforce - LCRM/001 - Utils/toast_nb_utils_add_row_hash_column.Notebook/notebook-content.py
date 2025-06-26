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
This PySpark notebook adds a `row_hash` column to an existing raw full Delta table 
for a specific Salesforce object (e.g., account, contact, member_group).

Purpose:
- Prepares the raw full table for incremental merge logic that relies on row hashing.
- Ensures existing historical data is preserved, with each row uniquely fingerprinted.
- Prevents the incremental merge notebook from overwriting the raw full table due to missing `row_hash`.

Behavior:
1. Reads the full raw Delta table for the given Salesforce object.
2. Computes a SHA-256 `row_hash` using all columns except `Id`.
3. Overwrites the raw full table with the same records, now including the `row_hash` column.

This notebook should be run once per object after initial full ingestion and before enabling incremental merges.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import sha2, concat_ws, col

spark = SparkSession.builder.getOrCreate()

object_name = "contract"
base_path = "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/a852188b-a853-4fd2-b6fb-541fa5469293/Tables/dbo"
raw_full_path = f"{base_path}/salesforce_lcrm_{object_name}_raw_full"

df = spark.read.format("delta").load(raw_full_path)

excluded_cols = {"Id"}
hash_cols = [c for c in df.columns if c not in excluded_cols]

df_with_hash = df.withColumn(
    "row_hash", sha2(concat_ws("||", *[col(c).cast("string") for c in hash_cols]), 256)
)

df_with_hash.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(raw_full_path)

print(f"Patched {object_name} raw_full table with row_hash.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
