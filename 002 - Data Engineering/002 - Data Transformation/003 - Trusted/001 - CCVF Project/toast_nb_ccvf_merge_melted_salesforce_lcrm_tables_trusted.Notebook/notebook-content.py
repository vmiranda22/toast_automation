# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e29a63e5-b594-4b3c-a005-d9dd6019942a",
# META       "default_lakehouse_name": "toast_lh_ccvf_trusted",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "e29a63e5-b594-4b3c-a005-d9dd6019942a"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# ---
# Notebook: toast_nb_merge_melted_settings_for_validation
#
# Description:
# Reads multiple long-form (melted) Delta tables representing Salesforce settings,
# standardizes their schema, and appends them into a unified table for use by the validation engine.
# Adds metadata fields to track setting source and type.
#
# Inputs:
# - member_group_settings_melted
# - member_group_product_fee_settings_melted
#
# Output:
# - member_group_settings_melted_all (partitioned by setting_type)
# ---

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

# === Parameters ===
trusted_lakehouse_id = "e29a63e5-b594-4b3c-a005-d9dd6019942a"
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"

def trusted_path(table_name: str) -> str:
    return f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{trusted_lakehouse_id}/Tables/dbo/{table_name}"

# === Load Melted Tables ===

# 1. Member Group Settings (Core)
df_core = spark.read.format("delta").load(trusted_path("salesforce_lcrm_member_group_settings_melted_trusted"))
df_core = (
    df_core
    .withColumn("setting_type", F.lit("group_core"))
    .withColumn("trusted_loaded_at", F.current_timestamp())
)

# 2. Product Fees
df_fees = spark.read.format("delta").load(trusted_path("salesforce_lcrm_salesforce_lcrm_product_fees_melted_trusted_trusted"))
df_fees = (
    df_fees
    .withColumn("setting_type", F.lit("product_fee"))
    .withColumn("trusted_loaded_at", F.current_timestamp())
)

# === Union Melted Tables ===
columns = ["MG_id", "MG_legacy_group_id", "salesforce_setting_name", "salesforce_setting_value", "setting_type", "trusted_loaded_at"]
df_union = df_core.select(columns).unionByName(df_fees.select(columns))

# === Write to Unified Validation Table (Partitioned) ===
df_union.write.format("delta") \
    .mode("append") \
    .partitionBy("setting_type") \
    .option("mergeSchema", "true") \
    .save(trusted_path("salesforce_lcrm_melted_all_fields"))

print("Melted settings appended to: salesforce_lcrm_melted_all_fields")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
