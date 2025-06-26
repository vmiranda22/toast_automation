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
# META         },
# META         {
# META           "id": "efc50c32-d3e3-46c5-aef1-78d9217f2f99"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

"""
Notebook: toast_nb_transform_raw_to_clean_salesforce_lcrm

Description:
This PySpark notebook automates the transformation of Salesforce raw Delta tables into cleaned versions
by applying a consistent normalization rule to all column names. This is part of a broader ETL process
in Microsoft Fabric where raw Salesforce objects are ingested and then standardized for downstream use.

Transformation Rules Applied to Column Names:
1. Convert all characters to lowercase.
2. Remove Salesforce-specific suffix '__c'.
3. Remove common Salesforce-managed prefixes such as 'SBQQ__'.
4. Insert underscores between lowercase and uppercase transitions (e.g., 'AccountId' → 'account_id').
5. If two columns normalize to the same name, a numeric suffix is added (e.g., 'tax_exempt', 'tax_exempt_1').

This version includes automatic resolution of duplicate column names during normalization, ensuring schema compatibility
while preserving all original fields.

Workflow:
1. A predefined list of Salesforce raw table names is iterated.
2. Each raw Delta table is loaded from the specified lakehouse using its ABFSS path.
3. Column names are transformed using the `normalize_column_name()` function, with automatic disambiguation.
4. The resulting DataFrame is written to a cleaned lakehouse with the updated schema and normalized column names.
5. The output table is named by replacing `_raw_full` with `_clean`.

Inputs:
- Raw Salesforce Delta tables with camelCase and Salesforce-style column names.
- `workspace_id`: Fabric workspace UUID.
- `lakehouse_id_raw`: UUID of the raw lakehouse containing input tables.
- `lakehouse_id_clean`: UUID of the cleaned lakehouse where results are stored.

Outputs:
- Cleaned Delta tables with normalized and disambiguated column names written to the cleaned lakehouse.

Usage:
This notebook is intended to be reused for batch processing of Salesforce raw tables by simply updating
the list of table names. It supports consistent naming conventions and reduces the need for manual column mappings.

Dropped from Facundo's notebook:
- Standardization of Boolean columns (e.g., mapping "Y"/"N" to True/False)
- Explicit data type casting
- Column reordering
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col
import re

# === Initialize Spark session ===
spark = SparkSession.builder.getOrCreate()

# === Configuration ===
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
lakehouse_id_raw = "a852188b-a853-4fd2-b6fb-541fa5469293"
lakehouse_id_clean = "efc50c32-d3e3-46c5-aef1-78d9217f2f99"

# === Utility: Normalize column name ===
def normalize_column_name(col_name: str) -> str:
    col_name = col_name.replace('__c', '')
    col_name = col_name.replace('SBQQ__', '')
    col_name = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', col_name)
    return col_name.lower()

def normalize_and_resolve_columns(df):
    """
    Transforms a DataFrame by normalizing column names and auto-resolving any naming collisions.
    """
    original_columns = df.columns
    normalized_counts = {}
    column_mappings = {}

    for orig in original_columns:
        norm = normalize_column_name(orig)
        count = normalized_counts.get(norm, 0)

        if count > 0:
            norm = f"{norm}_{count}"  # Append suffix to avoid collision

        column_mappings[norm] = orig
        normalized_counts[normalize_column_name(orig)] = count + 1

    return df.select([col(orig).alias(norm) for norm, orig in column_mappings.items()])

# === List of tables to process ===
tables = [
    "salesforce_lcrm_account_raw_full",
    "salesforce_lcrm_account_relationship_raw_full",
    "salesforce_lcrm_asset_raw_full",
    "salesforce_lcrm_case_raw_full",
    "salesforce_lcrm_contact_raw_full",
    "salesforce_lcrm_contract_raw_full",
    "salesforce_lcrm_member_group_raw_full",
    "salesforce_lcrm_member_group_role_raw_full",
    "salesforce_lcrm_opportunity_raw_full",
    "salesforce_lcrm_opportunity_product_raw_full",
    "salesforce_lcrm_product_raw_full",
    "salesforce_lcrm_plan-specific_fees_by_product_raw_full",
    "salesforce_lcrm_subscription_raw_full",
    "salesforce_lcrm_user_raw_full"
]

# === Transformation Loop ===
for table_name in tables:
    print(f"\nProcessing: {table_name}")
    try:
        # Load raw table
        df_raw = spark.read.format("delta").load(
            f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_raw}/Tables/dbo/{table_name}"
        )

        # Transform and normalize column names with validation
        df_clean = normalize_and_resolve_columns(df_raw)

        # Derive clean table name
        clean_table_name = table_name.replace("_raw", "_clean").replace("_full", "")

        # Write to clean lakehouse
        df_clean.write.format("delta") \
            .option("overwriteSchema", "true") \
            .mode("overwrite") \
            .save(f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_clean}/Tables/dbo/{clean_table_name}")

        print(f"Wrote clean table: {clean_table_name}")

    except Exception as e:
        print(f"Failed to process {table_name}: {e}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
