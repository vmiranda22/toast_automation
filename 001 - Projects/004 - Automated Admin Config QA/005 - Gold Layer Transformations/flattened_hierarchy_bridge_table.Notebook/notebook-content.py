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

from pyspark.sql.functions import split, explode, trim, col

group_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_group_information")

# Explode the ancestry column into organization_id → group_id mappings.
organization_group_map = (
    group_df
    .withColumn("org_id_array", split(col("ancestry"), "/"))
    .withColumn("org_id", explode(col("org_id_array")))
    .withColumn("org_id", trim(col("org_id")))
    .select(col("org_id").cast("string"), col("group_id").cast("string"))
    .distinct()
)

organization_group_map.write \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("flattened_hierarchy_bridge_table")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
