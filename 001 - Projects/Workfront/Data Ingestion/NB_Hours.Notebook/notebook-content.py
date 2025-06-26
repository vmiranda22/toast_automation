# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "fd91a974-12de-4aed-9135-cd6bfb991855",
# META       "default_lakehouse_name": "LH_Workfront",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "fd91a974-12de-4aed-9135-cd6bfb991855"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import col, explode_outer, lit, explode, regexp_replace, stack, expr
from pyspark.sql.types import ArrayType, StructType, StringType, MapType

spark.conf.set("spark.sql.caseSensitive", True)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.format("json") \
       .option("recursiveFileLookup", "true") \
       .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/fd91a974-12de-4aed-9135-cd6bfb991855/Files/JSON_Hours")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

flattened_df = df.select(explode(col("data")).alias("data")).select("data.*")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(flattened_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

filtered_df = flattened_df.select("ID", "entryDate", "hours", "lastUpdateDate", "objCode", "status", \
             col("owner.ID").alias("ownerID"), col("owner.name").alias("ownerName"), col("owner.objCode").alias("ownerObj"), \
             col("project.ID").alias("projectID"), col("project.name").alias("projectName"), col("project.objCode").alias("projectObj"), \
             col("task.ID").alias("taskID"), col("task.name").alias("taskName"), col("task.objCode").alias("taskObj"), col("task.DE:Time Type").alias("taskTimeType"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(filtered_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

filtered_df.write.format("delta").mode("append").save("Tables/flattened_hours")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
