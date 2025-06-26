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

# CELL ********************

from pyspark.sql.functions import col, split, explode, trim, count, sum, when, countDistinct

# Step 1: Load tables
group_settings = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_group_information")
compared_data = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/melted_comparison_dataset_200_silver_group_settings")

# Step 2: Join
joined_df = compared_data.join(
    group_settings.select("group_id", "ancestry"),
    compared_data["g_group_id"] == group_settings["group_id"],
    how="left"
)

# Step 3: Explode ancestry so each error maps to all its ancestor orgs
df_exploded = (
    joined_df.withColumn("org_id_array", split(col("ancestry"), "/"))
             .withColumn("org_id", explode(col("org_id_array")))
             .withColumn("org_id", trim(col("org_id")))
)

# Step 4: Flag no match
df_exploded = df_exploded.withColumn(
    "is_no_match", when(col("does_value_match") == "NO MATCH", 1).otherwise(0)
)

# Step 5: Aggregate per org: include distinct group count
org_error_stats = (
    df_exploded.groupBy("org_id")
    .agg(
        count("*").alias("total_settings_checked"),
        sum("is_no_match").alias("total_no_matches"),
        countDistinct("g_group_id").alias("total_groups")
    )
    .withColumn(
        "error_percentage",
        (col("total_no_matches") / col("total_settings_checked")) * 100
    )
)

org_error_stats.orderBy(col("error_percentage").desc()).show()
org_error_stats.write \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("org_error_percentages")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
