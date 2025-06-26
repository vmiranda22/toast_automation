# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "4b9a8e2d-64db-464e-b218-053f22ac13b1",
# META       "default_lakehouse_name": "fabrictest_lakehouse",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977"
# META     }
# META   }
# META }

# MARKDOWN ********************

# 
# #### Run the cell below to install the required packages for Copilot


# CELL ********************


#Run this cell to install the required packages for Copilot
%load_ext dscopilot_installer
%activate_dscopilot


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Import required resources.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, current_date, expr, first, lit, lower, posexplode, row_number, split, when
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, StringType, TimestampType
from pyspark.sql.window import Window

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Initialize SparkSession.

# CELL ********************

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "LEGACY")
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

sot_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/excel_sot_empire_life_of_canada")

display(sot_df)

# Get values in organization_id column

sot_organization_id = sot_df.select("organization_id").rdd.flatMap(lambda x: x).collect()

sot_organization_id = list(set(sot_organization_id))

sot_organization_id = sot_organization_id[0]

print(f"Unique values found in organization_id column: " + sot_organization_id)

# Get values in bill_to column

sot_bill_to = sot_df.select("bill_to").rdd.flatMap(lambda x: x).collect()

sot_bill_to = list(set(sot_bill_to))

sot_bill_to = sot_bill_to[0]

print(f"Unique values found in bill_to column: " + sot_bill_to)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

client_groups_df = spark.read.format("delta") \
                    .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_group_information") \
                    .filter(col("ancestry").contains(sot_organization_id))

display(client_groups_df)

# Print unique group_id

client_groups_unique_count = client_groups_df.select("group_id").distinct().count()

print(f"Unique values in group_id: {client_groups_unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

comparison_df = client_groups_df.select("group_id", "legacy_group_id", "bill_to", "membership_fee_type_cd") \
                .withColumn("is_bill_to_ok", when(col("bill_to").isNotNull(), "OK").otherwise("NOT OK")) \
                .withColumn("is_membership_fee_type_ok", when(col("membership_fee_type_cd") == "PEPM", "OK").otherwise("NOT OK"))

display(comparison_df)

bill_to_errors = (
    comparison_df
    .filter(col("is_bill_to_ok") == "NOT OK")
    .select("group_id")
    .distinct()
    .count()
)

membership_fee_type_errors = (
    comparison_df
    .filter(col("is_membership_fee_type_ok") == "NOT OK")
    .select("group_id")
    .distinct()
    .count()
)

groups_with_at_least_one_error = (
    comparison_df
    .filter((col("is_bill_to_ok") == "NOT OK") | (col("is_membership_fee_type_ok") == "NOT OK"))
    .select("group_id")
    .distinct()
    .count()
)

groups_with_both_errors = (
    comparison_df
    .filter((col("is_bill_to_ok") == "NOT OK") & (col("is_membership_fee_type_ok") == "NOT OK"))
    .select("group_id")
    .distinct()
    .count()
)

print(f"Number of group_id with at least one 'NOT OK': {groups_with_at_least_one_error}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # QA Stats

# CELL ********************

# QA STATS

percentage_of_groups_with_errors = round((groups_with_at_least_one_error / client_groups_unique_count) * 100, 2)

print(f"Total Empire Life of Canada Groups: {client_groups_unique_count}")
print(f"Number of Groups with at least 1 (one) error: {groups_with_at_least_one_error} ({percentage_of_groups_with_errors}% of the total Groups)")
print(f"Number of Groups with BILL TO errors: {bill_to_errors}")
print(f"Number of Groups with MEMBERSHIP FEE TYPE errors: {membership_fee_type_errors}")
print(f"Number of Groups with BOTH errors: {groups_with_both_errors}")

# print(f"% of Groups with at least 1 (one) error: {percentage_of_groups_with_errors}%")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
