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

# # Attempt at creating a compared dataset.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Initialize SparkSession.

# CELL ********************

spark = SparkSession.builder.getOrCreate()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Read Delta tables into Spark DataFrames.

# CELL ********************

df_lcrm_dataset = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/lcrm_dataset")
df_teladoc_eds_dataset = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dataset")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Function to rename columns using dictionary.

# CELL ********************

def rename_columns(df, rename_dict):
    """
    Renames multiple columns in a PySpark DataFrame based on a dictionary.

    Args:
        df (DataFrame): The input PySpark DataFrame.
        rename_dict (dict): Dictionary where keys are original column names, and values are new names.

    Returns:
        DataFrame: The DataFrame with renamed columns.
    """
    return df.select([col(c).alias(rename_dict.get(c, c)) for c in df.columns])

rename_dict_lcrm = {
    "MG_Name__c": "g_group_nm",
    "MG_Migration_Group_Number__c": "g_registration_group_cd"
}

rename_dict_teladoc = {
    "g_legacy_group_id": "MG_Group_Number__c"
}

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Apply function to dataframes.

# CELL ********************

df_lcrm_dataset = rename_columns(df_lcrm_dataset, rename_dict_lcrm)
df_teladoc_eds_dataset = rename_columns(df_teladoc_eds_dataset, rename_dict_teladoc)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Add suffix.

# CELL ********************

df_lcrm_dataset = df_lcrm_dataset.select([
    col(c).alias(c + "_salesforce") if c != "MG_Group_Number__c" else col(c)
    for c in df_lcrm_dataset.columns
])

df_teladoc_eds_dataset = df_teladoc_eds_dataset.select([
    col(c).alias(c + "_teladoc_eds") if c != "MG_Group_Number__c" else col(c)
    for c in df_teladoc_eds_dataset.columns
])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Join datasets.

# CELL ********************

df_compared_dataset = df_lcrm_dataset.join(df_teladoc_eds_dataset, on="MG_Group_Number__c", how="inner")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

columns_lcrm = set(df_lcrm_dataset.columns)
columns_teladoc = set(df_teladoc_eds_dataset.columns)


common_columns = [
    c for c in columns_lcrm if c.replace("_salesforce", "_teladoc_eds") in columns_teladoc
] + [
    c.replace("_salesforce", "_teladoc_eds") for c in columns_lcrm if c.replace("_salesforce", "_teladoc_eds") in columns_teladoc
]


columns_to_compare = [
    c for c in df_lcrm_dataset.columns 
    if c.endswith("_salesforce") and c.replace("_salesforce", "_teladoc_eds") in df_teladoc_eds_dataset.columns
]

comparison_exprs = [
    when(col(c) == col(c.replace("_salesforce", "_teladoc_eds")), True)
    .otherwise(False)
    .alias(c + "_comparison")
    for c in columns_to_compare
]

df_result = df_compared_dataset.select(
    col("MG_Group_Number__c"),
    *[col(c) for c in common_columns if c != "MG_Group_Number__c"],
    *comparison_exprs
)
df_result.show(1)

df_result.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("compared_dataset")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }
