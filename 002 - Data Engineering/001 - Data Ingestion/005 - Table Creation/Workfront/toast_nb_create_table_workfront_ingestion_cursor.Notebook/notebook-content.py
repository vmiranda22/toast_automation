# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "858ad52b-f017-4d74-9957-17175dd47103",
# META       "default_lakehouse_name": "toast_lh_workfront_raw",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "858ad52b-f017-4d74-9957-17175dd47103"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

spark.sql("""
CREATE TABLE IF NOT EXISTS workfront_ingestion_cursor (
    object_type STRING,
    last_ingested_at TIMESTAMP,
    updated_at TIMESTAMP
)
USING DELTA
""")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
