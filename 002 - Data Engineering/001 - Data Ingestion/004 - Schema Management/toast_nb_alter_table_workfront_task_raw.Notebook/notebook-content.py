# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

table_name = "workfront_task_raw"

# List of columns to be added (column_name, data_type):
columns_to_add = [
    ("assignedToID", "STRING"),
    ("description", "STRING")
]

alter_table_sql = f"""
ALTER TABLE {table_name}
ADD COLUMNS (
    {', '.join([f"{col_name} {col_type}" for col_name, col_type in columns_to_add])}
)
"""

print(f"Running ALTER TABLE to add columns to {table_name}...")
spark.sql(alter_table_sql)
print("ALTER TABLE completed successfully.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
