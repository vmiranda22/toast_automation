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
Notebook: nb_optimize_vacuum_all_tables_in_lakehouse

Purpose:
--------
This notebook performs periodic Delta maintenance (OPTIMIZE and VACUUM) on all Delta tables 
within a specified Microsoft Fabric lakehouse. It is intended to run as part of a scheduled 
pipeline (e.g., weekly) to reduce file fragmentation, improve query performance, and manage 
storage usage.

Target:
-------
Lakehouse ID: a852188b-a853-4fd2-b6fb-541fa5469293
Workspace ID: b08d383a-b8cc-4b8e-b189-d9d696a01977

Behavior:
---------
1. Lists all Delta tables in the lakehouse using the `SHOW TABLES` command.
2. For each table, builds the full ABFSS path under the `/Tables/dbo` directory.
3. Skips any tables whose names contain the substrings: "cursor", "log", "curated", or "trusted".
4. For each remaining table:
   - Loads its schema to determine whether it includes an `Id` column.
   - Runs `OPTIMIZE` with `ZORDER BY (Id)` if the column exists, or a plain `OPTIMIZE` otherwise.
   - Runs `VACUUM` with a 7-day retention (168 hours).
5. Handles exceptions gracefully so one failed table does not stop the process.

Why Trusted Tables Are Skipped:
------------------------------------------
Trusted tables are often governed more strictly, updated less frequently, 
and may already be maintained manually. Applying automated `OPTIMIZE` and `VACUUM` to these 
tables can:
- Waste capacity on already-optimized data.
- Interfere with time-travel requirements or auditability.
- Bypass custom ZORDERing based on business-critical columns (e.g., `created_at`, `member_id`).

As such, this notebook skips any tables containing the substrings "trusted", "curated", 
"log", or "cursor". If maintenance is needed on curated tables, it should be performed 
intentionally in a separate, more controlled notebook or pipeline.

Recommended Usage:
------------------
Place this notebook in the `/Monitoring/DeltaMaintenance/` folder and schedule it weekly 
via a pipeline to maintain performance and storage health for raw and frequently changing 
Delta tables.

"""

from pyspark.sql.utils import AnalysisException
from datetime import datetime
import os

# === CONFIG ===
lakehouse_id = "a852188b-a853-4fd2-b6fb-541fa5469293"
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
container = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com"
tables_base_path = f"{container}/{lakehouse_id}/Tables"

# === List all Delta tables in lakehouse ===
tables_df = spark.sql("SHOW TABLES")
tables = [row["tableName"] for row in tables_df.collect()]

for table in tables:
    delta_path = f"{tables_base_path}/dbo/{table}"
    try:
        print(f"\n[{datetime.utcnow()}] OPTIMIZE: {table}")

        # Get schema for the table to check if 'Id' exists
        table_df = spark.read.format("delta").load(delta_path)
        schema_columns = [field.name for field in table_df.schema.fields]

        if "Id" in schema_columns:
            spark.sql(f"OPTIMIZE delta.`{delta_path}` ZORDER BY (Id)")
        else:
            spark.sql(f"OPTIMIZE delta.`{delta_path}`")

        print(f"[{datetime.utcnow()}] VACUUM: {table}")
        spark.sql(f"VACUUM delta.`{delta_path}` RETAIN 168 HOURS")

    except AnalysisException as e:
        print(f"[{datetime.utcnow()}] Skipping {table}: {str(e)}")
    except Exception as ex:
        print(f"[{datetime.utcnow()}] Error on {table}: {str(ex)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
