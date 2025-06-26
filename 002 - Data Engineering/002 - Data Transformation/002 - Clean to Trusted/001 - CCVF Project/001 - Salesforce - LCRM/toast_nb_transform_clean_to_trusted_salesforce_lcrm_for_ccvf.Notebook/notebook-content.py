# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "efc50c32-d3e3-46c5-aef1-78d9217f2f99",
# META       "default_lakehouse_name": "toast_lh_salesforce_lcrm_clean",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "efc50c32-d3e3-46c5-aef1-78d9217f2f99"
# META         },
# META         {
# META           "id": "e29a63e5-b594-4b3c-a005-d9dd6019942a"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# object_prefixes = {
#     "account": "ACCT_",
#     "account_relationship": "ACCT_REL_",
#     "asset": "ASSET_",
#     "case": "CASE_",
#     "member_group": "MG_",
#     "member_group_role": "MGR_",
#     "opportunity": "OPP_",
#     "opportunity_product": "OPP_PROD_",
#     "plan-specific_fees_by_product": "PSF_",
#     "product": "PROD_",
#     "subscription": "SUB_",
#     "contact": "CON_",
#     "contract": "CNTRCT_",
#     "organization": "ORG_"
# }

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, concat, expr, current_timestamp
from collections import defaultdict

# === Spark Session ===
spark = SparkSession.builder.getOrCreate()

# === PARAMETERS ===
trusted_lakehouse_id = "e29a63e5-b594-4b3c-a005-d9dd6019942a"
clean_lakehouse_id = "efc50c32-d3e3-46c5-aef1-78d9217f2f99"
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"

def table_path(table_name: str, layer: str = "clean") -> str:
    """
    Constructs the full ABFSS path for a given table and layer.
    """
    lakehouse_id = clean_lakehouse_id if layer == "clean" else trusted_lakehouse_id
    return f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/dbo/salesforce_lcrm_{table_name}_{layer}"

def trusted_path(table_name: str) -> str:
    """
    Shortcut for retrieving the path to the trusted version of a given table.
    """
    return table_path(table_name, layer="trusted")

from pyspark.sql import functions as F

def add_prefix(df, prefix: str) -> "DataFrame":
    """
    Adds a prefix to all column names in the given DataFrame.

    Parameters:
    - df (DataFrame): Input PySpark DataFrame.
    - prefix (str): Prefix to prepend to column names.

    Returns:
    - DataFrame: DataFrame with prefixed column names.
    """
    return df.select([F.col(c).alias(f"{prefix}{c}") for c in df.columns])

# === UTILITY: Apply Column Renames ===
def apply_column_renames(df, rename_map: dict):
    for old_col, new_col in rename_map.items():
        if old_col in df.columns:
            df = df.withColumnRenamed(old_col, new_col)
    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load the mapping table from the trusted lakehouse
df_mapping = spark.read.format("delta").load(trusted_path("to_admin_field_mappings"))

# Convert to nested dictionary: { salesforce_lcrm_object: { salesforce_lcrm_field_name: salesforce_lcrm_field_friendly_name, ... }, ... }
mapping_dict = defaultdict(dict)

for row in df_mapping.collect():
    mapping_dict[row["salesforce_lcrm_object"]][row["salesforce_lcrm_field_name"]] = row["salesforce_lcrm_field_friendly_name"]

clean_to_trusted_name_mapping = dict(mapping_dict)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the cleaned 'member_group' table into its trusted form by applying business logic and standardized mappings.

Steps:
1. Loads the 'member_group' cleaned table using a predefined path.
2. Applies column renaming using the configured clean-to-trusted field mapping.
3. Computes a new 'dependent_eligibility' column:
   - If dependents are included, inherits from 'primary_eligibility'.
   - Otherwise, defaults to 'Open'.
4. Normalizes marketing opt-in flags (e.g., 'email', 'text_sms') to 'Opt In' or 'Opt Out'.
5. Standardizes null values in 'enable_chronic_care_referrals' to the string 'None'.
6. Maps country codes (e.g., 'USA' → 'United States Of America') for 'domestic_country'.
7. Ensures 'legacy_group_id' is non-null by prefixing nulls with 'null_' and using the record ID.
8. Appends 'trusted_loaded_at' with the current timestamp to track when the record was transformed.
9. Writes the transformed DataFrame to the trusted Lakehouse layer, overwriting the previous version.
"""

table_key = "member_group"
df_member_group = spark.read.format("delta").load(table_path(table_key))
df_member_group = apply_column_renames(df_member_group, clean_to_trusted_name_mapping[table_key])

# === Trusted transformation ===
df_member_group = df_member_group.withColumn(
    "mg_dependent_eligibility",
    when(col("mg_dependents_included") == True, col("mg_primary_eligibility"))
    .otherwise(lit("Open")).cast("string")
).drop("mg_dependents_included")

marketing_columns = ["mg_direct_mail", "mg_email", "mg_text_sms", "mg_incentives_opt_in"]
df_member_group = df_member_group.select(
    *[
        when(col(c) == True, "Opt In").otherwise("Opt Out").alias(c) if c in marketing_columns else col(c)
        for c in df_member_group.columns
    ]
)

df_member_group = df_member_group.withColumn(
    "mg_domestic_country",
    when(col("mg_domestic_country") == "USA", "United States Of America")
    .when(col("mg_domestic_country") == "CAN", "Canada")
    .otherwise(col("mg_domestic_country"))
)

# Add transformation timestamp
df_member_group = df_member_group.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_member_group = df_member_group.drop("row_hash")

# Write to trusted layer
df_member_group.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'member_group_role' table into its trusted version by applying renaming rules,
enriching with descriptive names from related tables, and appending a transformation timestamp.

Steps:
1. Loads the cleaned 'member_group_role' table using the standardized table path.
2. Applies clean-to-trusted column renaming.
3. Loads supporting 'account' and 'member_group' clean tables for lookup enrichment.
4. Enriches with 'member_group_nm' from the member_group table and 'source_account_nm' from the account table.
5. Selects and orders trusted columns relevant for downstream consumption.
6. Appends 'trusted_loaded_at' with the current timestamp to track the transformation time.
7. Writes the final trusted DataFrame back to the trusted Lakehouse layer.
"""

from pyspark.sql.functions import current_timestamp

table_key = "member_group_role"

# Load and rename columns in clean member_group_role table
df_member_group_role = spark.read.format("delta").load(table_path(table_key))
df_member_group_role = apply_column_renames(df_member_group_role, clean_to_trusted_name_mapping[table_key])

# Load supporting account and member_group tables for join enrichment
df_account_clean = spark.read.format("delta").load(table_path("account"))
df_account_clean = df_account_clean.select("id", "name").withColumnsRenamed({"id": "ACCT_id", "name": "source_account_nm"})

df_member_group_clean = spark.read.format("delta").load(table_path("member_group"))
df_member_group_clean = df_member_group_clean.select("id", "name").withColumnsRenamed({"id": "MG_id", "name": "member_group_nm"})

# Join with member_group table to enrich with member_group_nm
df_member_group_role = df_member_group_role.join(
    df_member_group_clean,
    df_member_group_role["mgr_member_group_id"] == df_member_group_clean["MG_id"],
    "left_outer"
).drop("MG_id")

# Join with account table to enrich with source_account_nm
df_member_group_role = df_member_group_role.join(
    df_account_clean,
    df_member_group_role["mgr_source_account_id"] == df_account_clean["ACCT_id"],
    "left_outer"
).drop("ACCT_id")

# Reorder and select final trusted columns
df_member_group_role = df_member_group_role.select(
    "mgr_id", "name", "role_type",
    "mgr_member_group_id", "member_group_nm", "mgr_member_group_status",
    "mgr_source_account_id", "source_account_nm"
)

# Add transformation timestamp
df_member_group_role = df_member_group_role.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_member_group_role = df_member_group_role.drop("row_hash")

# Write to trusted layer
df_member_group_role.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Normalizes the 'opportunity' table by truncating Salesforce IDs and applying standardized column mappings.

Steps:
1. Loads the 'opportunity' cleaned table using a predefined path.
2. Applies column renaming based on the clean-to-trusted mapping.
3. Truncates the 'id' field to 15 characters to match the standard SFDC ID format.
4. Adds a 'trusted_loaded_at' timestamp column to track when the record was transformed.
5. Overwrites the table in-place in the clean Lakehouse layer.
"""

table_key = "opportunity"

# Load clean opportunity table
df_opportunity = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_opportunity = apply_column_renames(df_opportunity, clean_to_trusted_name_mapping[table_key])

# Truncate ID to 15 characters (standard SFDC ID length)
df_opportunity = df_opportunity.withColumn("opp_id", expr("substring(opp_id, 1, 15)"))

# Add transformation timestamp
df_opportunity = df_opportunity.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_opportunity = df_opportunity.drop("row_hash")

# Overwrite with updated records
df_opportunity.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'opportunity_product' table by applying field renaming,
standardizing the 'opportunity_id' to 15-character Salesforce ID format,
and tracking transformation time.

Steps:
1. Loads the cleaned 'opportunity_product' table using the standardized table path.
2. Applies clean-to-trusted column renaming.
3. Truncates the 'opportunity_id' to 15 characters (standard Salesforce ID length).
4. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
5. Writes the updated table back to the clean Lakehouse layer, overwriting the existing data.
"""

table_key = "opportunity_product"

# Load clean opportunity_product table
df_opportunity_product = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_opportunity_product = apply_column_renames(df_opportunity_product, clean_to_trusted_name_mapping[table_key])

# Truncate opportunity_id to 15 characters (standard SFDC ID length)
df_opportunity_product = df_opportunity_product.withColumn(
    "opportunity_id",
    expr("substring(opportunity_id, 1, 15)")
)

# Add transformation timestamp
df_opportunity_product = df_opportunity_product.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_opportunity_product = df_opportunity_product.drop("row_hash")

# Overwrite with updated records
df_opportunity_product.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'account' table by applying standardized field renaming
and tracking the time of transformation.

Steps:
1. Loads the cleaned 'account' table using the standardized table path.
2. Applies clean-to-trusted column renaming based on the configured mapping.
3. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
4. Writes the updated DataFrame to the trusted Lakehouse layer, overwriting any existing data.
"""

table_key = "account"

# Load clean account table
df_account = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_account = apply_column_renames(df_account, clean_to_trusted_name_mapping[table_key])

# Add transformation timestamp
df_account = df_account.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_account = df_account.drop("row_hash")

# Write to trusted layer
df_account.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'account_relationship' table by applying standardized column renaming
and tracking the time of transformation.

Steps:
1. Loads the cleaned 'account_relationship' table using the standardized table path.
2. Applies clean-to-trusted column renaming using the configured mapping.
3. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
4. Writes the transformed DataFrame to the trusted Lakehouse layer, overwriting any existing version.
"""

table_key = "account_relationship"

# Load clean account_relationship table
df_acct_rel = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_acct_rel = apply_column_renames(df_acct_rel, clean_to_trusted_name_mapping[table_key])

# Add transformation timestamp
df_acct_rel = df_acct_rel.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_acct_rel = df_acct_rel.drop("row_hash")

# Write to trusted layer
df_acct_rel.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'asset' table by applying standardized column renaming
and recording the time of the transformation.

Steps:
1. Loads the cleaned 'asset' table using the standardized table path.
2. Applies clean-to-trusted column renaming using the configured mapping.
3. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
4. Writes the updated DataFrame to the trusted Lakehouse layer, overwriting any existing version.
"""

table_key = "asset"

# Load clean asset table
df_asset = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_asset = apply_column_renames(df_asset, clean_to_trusted_name_mapping[table_key])

# Add transformation timestamp
df_asset = df_asset.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_asset = df_asset.drop("row_hash")

# Write to trusted layer
df_asset.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'case' table by applying standardized column renaming
and recording the time of the transformation.

Steps:
1. Loads the cleaned 'case' table using the standardized table path.
2. Applies clean-to-trusted column renaming using the configured mapping.
3. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
4. Writes the updated DataFrame to the trusted Lakehouse layer, overwriting any existing version.
"""

table_key = "case"

# Load clean case table
df_case = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_case = apply_column_renames(df_case, clean_to_trusted_name_mapping[table_key])

# Add transformation timestamp
df_case = df_case.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_case = df_case.drop("row_hash")

# Write to trusted layer
df_case.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'plan-specific_fees_by_product' table by applying standardized column renaming
and recording the time of the transformation.

Steps:
1. Loads the cleaned 'plan-specific_fees_by_product' table using the standardized table path.
2. Applies clean-to-trusted column renaming using the configured mapping.
3. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
4. Drops inherited technical columns like 'row_hash'.
5. Adds a standardized prefix to all columns to avoid name collisions during joins.
6. Writes the updated DataFrame to the trusted Lakehouse layer, overwriting any existing version.
"""

table_key = "plan-specific_fees_by_product"

# Load clean table
df_psf = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_psf = apply_column_renames(df_psf, clean_to_trusted_name_mapping[table_key])

# Add transformation timestamp
df_psf = df_psf.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_psf = df_psf.drop("row_hash")

# Write to trusted layer
df_psf.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'subscription' table by applying standardized column renaming
and recording the time of the transformation.

Steps:
1. Loads the cleaned 'subscription' table using the standardized table path.
2. Applies clean-to-trusted column renaming using the configured mapping.
3. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
4. Drops inherited technical columns like 'row_hash'.
5. Adds a standardized prefix to all columns to avoid name collisions during joins.
6. Writes the updated DataFrame to the trusted Lakehouse layer, overwriting any existing version.
"""

table_key = "subscription"

# Load clean subscription table
df_subscription = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_subscription = apply_column_renames(df_subscription, clean_to_trusted_name_mapping[table_key])

# Add transformation timestamp
df_subscription = df_subscription.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_subscription = df_subscription.drop("row_hash")

# Write to trusted layer
df_subscription.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the 'product' table by applying standardized column renaming
and recording the time of the transformation.

Steps:
1. Loads the cleaned 'product' table using the standardized table path.
2. Applies clean-to-trusted column renaming using the configured mapping.
3. Appends 'trusted_loaded_at' with the current timestamp to track transformation time.
4. Drops inherited technical columns like 'row_hash'.
5. Adds a standardized prefix to all columns to avoid name collisions during joins.
6. Writes the updated DataFrame to the trusted Lakehouse layer, overwriting any existing version.
"""

table_key = "product"

# Load clean product table
df_product = spark.read.format("delta").load(table_path(table_key))

# Apply any configured column renames
df_product = apply_column_renames(df_product, clean_to_trusted_name_mapping.get(table_key, {}))

# Add transformation timestamp
df_product = df_product.withColumn("trusted_loaded_at", current_timestamp())

# Drop inherited row_hash if present
df_product = df_product.drop("row_hash")

# Write to trusted layer
df_product.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path(table_key))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
