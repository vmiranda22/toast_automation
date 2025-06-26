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
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "4b9a8e2d-64db-464e-b218-053f22ac13b1"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, col
from pyspark.sql.types import StringType

# Start Spark session
spark = SparkSession.builder.getOrCreate()

# Step 1: Get all table names in the catalog
all_tables = spark.sql("SHOW TABLES").filter(col("tableName").contains("salesforce_uat_100_bronze"))

# Step 2: Collect tables to driver
table_list = all_tables.select("tableName").rdd.flatMap(lambda x: x).collect()

# Step 3: Extract columns from each table
results = []
for table_name in table_list:
    try:
        # Get the list of columns
        df = spark.table(table_name)
        columns = [field.name for field in df.schema.fields]
        column_list_str = ", ".join(columns)
        results.append((table_name, column_list_str))
    except Exception as e:
        print(f"Error processing table {table_name}: {e}")

# Step 4: Create a DataFrame with the results
results_df = spark.createDataFrame(results, ["table_name", "table_columns"])

display(results_df)

# Step 5: Save the result as a table (overwrite if exists)
# results_df.write.mode("overwrite").saveAsTable("salesforce_uat_100_column_inventory")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
