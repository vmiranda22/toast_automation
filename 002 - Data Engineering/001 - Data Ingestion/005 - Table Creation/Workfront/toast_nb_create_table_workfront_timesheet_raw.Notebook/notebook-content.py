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
# META     },
# META     "warehouse": {
# META       "default_warehouse": "0d50be10-2e1a-4c74-a4e8-d8819668d36b",
# META       "known_warehouses": [
# META         {
# META           "id": "0d50be10-2e1a-4c74-a4e8-d8819668d36b",
# META           "type": "Lakewarehouse"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import sha2, concat_ws, col
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, ArrayType
from collections import defaultdict
import re

spark = SparkSession.builder.getOrCreate()

timestamp_columns_raw = {
    "startDate", "endDate", "lastUpdateDate"
}

array_columns_raw = {"auditTypes"}

def sanitize_column(name, used_names, suffix_counter):
    sanitized = re.sub(r"[^\w]", "_", name).lower()
    base = sanitized
    while sanitized in used_names:
        suffix_counter[base] += 1
        sanitized = f"{base}_{suffix_counter[base]}"
    used_names.add(sanitized)
    return sanitized

base_columns_raw = [
    "ID", "displayName", "objCode", "approverCanEditHours", "approverID",
    "customerID", "endDate", "extRefID", "hasNotes", "hoursDuration",
    "isOvertimeDisabled", "lastNoteID", "lastUpdateDate", "lastUpdatedByID",
    "overtimeHours", "regularHours", "startDate", "status",
    "timesheetProfileID", "totalDays", "totalHours", "userID"
]

all_columns_raw = base_columns_raw + ["row_hash"]

suffix_counter = defaultdict(int)
used_names = set()
raw_to_sanitized = {
    raw: sanitize_column(raw, used_names, suffix_counter)
    for raw in all_columns_raw
}
timestamp_columns_sanitized = {
    raw_to_sanitized[f] for f in timestamp_columns_raw if f in raw_to_sanitized
}
array_columns_sanitized = {
    raw_to_sanitized[f] for f in array_columns_raw if f in raw_to_sanitized
}

schema = StructType([
    StructField(
        raw_to_sanitized[raw],
        ArrayType(StringType()) if raw_to_sanitized[raw] in array_columns_sanitized
        else TimestampType() if raw_to_sanitized[raw] in timestamp_columns_sanitized
        else StringType(),
        False if raw == "ID" else True
    )
    for raw in all_columns_raw
])

empty_df = spark.createDataFrame([], schema)
empty_df.write.format("delta").mode("ignore").saveAsTable("workfront_timesheet_raw")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
