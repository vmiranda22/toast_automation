# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "5c03804a-6817-4f61-bdd3-d666573c958a",
# META       "default_lakehouse_name": "toast_gab_lh_dev",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "5c03804a-6817-4f61-bdd3-d666573c958a"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import StructType
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, StringType, StructField, TimestampType

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

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

schema = StructType([
    StructField("activity_id", StringType(), True),
    StructField("activity_name", StringType(), True),
    StructField("activity_type", StringType(), True),
    StructField("activity_run_id", StringType(), True),
    StructField("activity_run_status", StringType(), True),
    StructField("activity_run_start_timestamp", StringType(), True),
    StructField("activity_run_end_timestamp", StringType(), True),
])

data = [("testid", "testname", "testtype", "testrunid", "testrunstatus", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]

audit_log_df = spark.createDataFrame(data, schema)

# Save table to Lakehouse
audit_log_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/gab_pipeline_activities_audit_log")

display(audit_log_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
