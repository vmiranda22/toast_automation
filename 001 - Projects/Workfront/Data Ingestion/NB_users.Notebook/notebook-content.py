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
from pyspark.sql import functions as sf

spark.conf.set("spark.sql.caseSensitive", True)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.format("json") \
       .option("recursiveFileLookup", "true") \
       .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/fd91a974-12de-4aed-9135-cd6bfb991855/Files/JSON_users")

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

flattened_df = flattened_df.sort(sf.desc("lastUpdateDate"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

flattened_df = flattened_df.dropDuplicates(['ID'])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

ids_array = [str(row.ID) for row in flattened_df.collect()]

ids_str = ",".join(f"'{id}'" for id in ids_array)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

query = f"""
DELETE FROM LH_Workfront.flattened_users
WHERE ID IN ({ids_str})
"""

result = spark.sql(query)

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

mg_df = flattened_df.withColumn('managerName',col('manager.name'))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(mg_df.drop('manager'))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

mg_df.write.format("delta").mode("append").save("Tables/flattened_users")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
