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
import pyspark.sql.functions as F
from pyspark.sql.types import ArrayType, StructType, StringType, MapType
import pandas as pd

spark.conf.set("spark.sql.caseSensitive", True)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.format("json") \
       .option("recursiveFileLookup", "true") \
       .load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/fd91a974-12de-4aed-9135-cd6bfb991855/Files/JSON")

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

paramValues_df = flattened_df.select('ID', 'parameterValues')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

flattened_df = flattened_df.drop('auditTypes', 'parameterValues', )

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

flattened_df.write.format("delta").mode("append").save("Tables/flattened_issues")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

filtered_paramValues = paramValues_df.select("ID", 'parameterValues.*')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

filtered_paramValues = filtered_paramValues.toDF(*[col.lower().replace(" ", "").replace(",", "").replace("'", "").replace("-", "").replace("#", "").replace("DE:", "").replace(".", "").replace("/", "_") for col in filtered_paramValues.columns])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(filtered_paramValues)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

cast_exprs = [f"cast({col} as string) as {col}" for col in value_cols]
filtered_paramValues_casted = filtered_paramValues.selectExpr(pivot_col, *cast_exprs)

melted_df = filtered_paramValues_casted.selectExpr(
    pivot_col,
    "stack({0}, {1}) as (paramValue, Value)".format(
        len(value_cols),
        ", ".join([f"'{col}', {col}" for col in value_cols])
    )
)

melted_df = melted_df.dropna(subset=["Value"])

display(melted_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

filtered_paramValues = filtered_paramValues.drop('requestedgolivedate', 'projectnotes', "ca,dateaddt'l")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

filtered_paramValues.write.format("delta").mode("append").save("Tables/flattened_paramValues")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
