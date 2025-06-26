# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e29a63e5-b594-4b3c-a005-d9dd6019942a",
# META       "default_lakehouse_name": "toast_lh_ccvf_trusted",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "e29a63e5-b594-4b3c-a005-d9dd6019942a"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# See if these merges and transformations can be moved into the toast_nb_transform_clean_to_trusted_salesforce_lcrm_for_ccvf. There's already data enrichment for the member_group table there. Or remove the enrichment of the member_group table from that notebook and only leave promotion to trusted layer.

# CELL ********************

# === Spark Session ===
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
spark = SparkSession.builder.getOrCreate()

# === PARAMETERS ===
trusted_lakehouse_id = "e29a63e5-b594-4b3c-a005-d9dd6019942a"
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"

# === Utility: Trusted Path Builder ===
def trusted_path(table_name: str) -> str:
    return f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{trusted_lakehouse_id}/Tables/dbo/salesforce_lcrm_{table_name}_trusted"

# === Load Trusted Tables ===
df_account       = spark.read.format("delta").load(trusted_path("account"))
df_member_group  = spark.read.format("delta").load(trusted_path("member_group"))
df_fees          = spark.read.format("delta").load(trusted_path("plan-specific_fees_by_product"))
df_subscription  = spark.read.format("delta").load(trusted_path("subscription"))
df_product       = spark.read.format("delta").load(trusted_path("product"))

# Prefilter the PSF (df_fees) table
df_fees = df_fees.filter(F.col("PSF_product_end_date").isNull())

# === Join account → member_group → plan_specific_fees_by_product ===
df_combined = df_account.join(
    df_member_group,
    df_account["acct_id"] == df_member_group["mg_account_id"],
    how="inner"
).join(
    df_fees,
    df_member_group["mg_id"] == df_fees["psf_member_group_id"],
    how="inner"
).join(
    df_subscription,
    df_fees["psf_subscription_id"] == df_subscription["sub_id"],
    how="left"
).join(
    df_product,
    df_subscription["sub_product"] == df_product["prod_id"],
    how="left"
)
"""
# === Select Final Fields ===
df_combined = df_combined.select(
    # Member Group Info
    "mg_id", "mg_legacy_group_id",

    # Account Info
    "acct_id",

    # Fee Plan Info
    "psf_id", "psf_currency_iso_code", "psf_print_or_less", "psf_client_retail_fee",
    "psf_consult_fee_initial_diagnostic_mbr_pd", "psf_consult_fee_initial_diagnostic_plan_pd",
    "psf_visit_fee_member", "psf_consult_fee_ongoing_md_mbr_pd", "psf_consult_fee_ongoing_md_plan_pd",
    "psf_consult_fee_ongoing_non_md_mbr_pd", "psf_consult_fee_ongoing_non_md_plan_pd",
    "psf_visit_fee_client", "psf_current_membership_fee", "psf_dermconsult_fee_mbr_pd",
    "psf_dermconsult_fee_plan_pd", "psf_legacy_group_id", "psf_membership_fee", "psf_product_end_date",
    "psf_product_start_date", "psf_product", "psf_teladoc_net_fee", "psf_asset_name", "psf_is_fee_matched",
    "psf_product_code", "psf_disable_coaching", "psf_disable_teletherapy", "psf_pg", "psf_derm_100_covered",
    "psf_gm_100_covered", "psf_mh_100_covered", "psf_bill_to_account", "psf_payer_account", "psf_sold_to_account",
    "psf_bill_to_account_guid", "psf_payer_account_guid", "psf_sold_to_account_guid", "psf_usgh_app_opt_out",

    # Subscription Info
    "sub_id", "sub_currency_iso_code", "sub_additional_discount_amount", "sub_bundle", "sub_product_name", "sub_product",
    "sub_quantity", "sub_pricing_method", "sub_consult_type", "sub_current_membership_fee", "sub_fee_type", "sub_membership_fee",

    # Product Info
    "prod_id", "prod_name"
).orderBy("mg_legacy_group_id", "prod_name")"""

# Filter to specific Member Group ID
df_filtered = df_combined.filter(df_combined["MG_id"] == "a1I5G00000CEw2uUAD")

# Display the result (Fabric/Databricks)
display(df_filtered)

# === Write to Trusted Table ===
output_table_name = "salesforce_lcrm_product_fees_view"

df_combined.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{trusted_lakehouse_id}/Tables/dbo/salesforce_lcrm_{output_table_name}_trusted")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

# === Step 1: Retain only the identifiers used in the first melt ===
# Ensure MG_legacy_group_id exists in df_combined or join it from df_group_info
required_ids = ["mg_id", "mg_legacy_group_id"]
available_ids = [col for col in required_ids if col in df_combined.columns]

# Define setting columns by excluding the retained identifiers
excluded_columns = available_ids
setting_columns = [col for col in df_combined.columns if col not in excluded_columns]

# === Step 2: Cast all setting columns to STRING ===
for col_name in setting_columns:
    df_combined = df_combined.withColumn(col_name, F.col(col_name).cast("STRING"))

# === Step 3: Construct the stack expression ===
stack_expr = f"stack({len(setting_columns)}, " + ", ".join([f"'{col}', {col}" for col in setting_columns]) + ")"

# === Step 4: Apply melting ===
df_melted = df_combined.select(
    *available_ids,
    F.expr(stack_expr).alias("salesforce_setting_name", "salesforce_setting_value")
)

# === Step 5: Clean up ===
df_melted = (
    df_melted
    .withColumn("salesforce_setting_value", F.trim(F.col("salesforce_setting_value")))
    .dropDuplicates(["mg_id", "mg_legacy_group_id", "salesforce_setting_name", "salesforce_setting_value"])
    .dropna(subset=["mg_id", "mg_legacy_group_id"])
    .orderBy("MG_id", "salesforce_setting_name")
)

# === Step 6: Write to Trusted Layer ===
df_melted.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path("salesforce_lcrm_product_fees_melted_trusted"))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
