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

# MARKDOWN ********************

# # Products Information (Fees + Settings Merged)

# MARKDOWN ********************

# ### Import required resources.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, collect_list, concat, contains, expr, first, lit, regexp_extract, sum, when
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, StringType, TimestampType
from pyspark.sql.window import Window

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Initialize SparkSession.

# CELL ********************

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "LEGACY")
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Load required tables.

# CELL ********************

# Group Service Specialty Relations

products_fees_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_products_fees_information")

products_settings_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_products_settings_information")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# CELL ********************

def add_prefix(df, prefix):
    """
    Adds a prefix to all column names in a PySpark DataFrame.

    Args:
    df (DataFrame): The input PySpark DataFrame.
    prefix (str): The prefix to add.

    Returns:
    DataFrame: A new DataFrame with renamed columns.
    """
    renamed_columns = [col(c).alias(f"{prefix}{c}") for c in df.columns]
    
    return df.select(*renamed_columns)

products_fees_df = add_prefix(products_fees_df, "PF_")
products_settings_df = add_prefix(products_settings_df, "PS_")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

### Print row count

row_count = products_fees_df.count()

print(f"Total rows in Products Fees table: {row_count}")

### Print unique group_id

unique_count = products_fees_df.select("PF_group_id").distinct().count()

print(f"Unique values in group_id column in Products Fees table: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

### Print row count

row_count = products_settings_df.count()

print(f"Total rows in Products Settings table: {row_count}")

### Print unique group_id

unique_count = products_settings_df.select("PS_group_id").distinct().count()

print(f"Unique values in group_id column in Products Settings table: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

products_all_information_df = products_fees_df.join(
    products_settings_df,
    (col("PF_group_id") == col("PS_group_id")) & (col("PF_service_specialty_feature_cd") == col("PS_service_specialty_feature_cd")),
    "left_outer"
)

display(products_all_information_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

### Print row count

row_count = products_all_information_df.count()

print(f"Total rows in Products Settings table: {row_count}")

### Print unique group_id

unique_count = products_all_information_df.select("PF_group_id").distinct().count()

print(f"Unique values in group_id column in ALL Products table: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

products_all_information_df = products_all_information_df.drop(
                                "PS_group_id",
                                "PS_group_service_specialty_relation_id",
                                "PS_service_specialty_cd",
                                "PS_service_specialty_nm",
                                "PS_group_service_specialty_feature_relation_id",
                                "PS_service_specialty_feature_cd",
                                "PS_service_specialty_feature_nm"
                            )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

### Print row count

row_count = products_all_information_df.count()

print(f"Total rows in Products Settings table: {row_count}")

### Print unique group_id

unique_count = products_all_information_df.select("PF_group_id").distinct().count()

print(f"Unique values in group_id column in ALL Products table: {unique_count}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(products_all_information_df.filter(col("PF_group_id") == "9950"))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Save to Lakehouse with new Schema.

# CELL ********************

products_all_information_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_products_all_information")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
