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

# CELL ********************

"""
Joins CCVF-trusted `account` and `member_group` tables to produce a unified view
of group-level configuration enriched with account details.

Steps:
1. Load prefixed, trusted `account` and `member_group` tables using workspace and lakehouse parameters.
2. Join on `id = account_id`.
3. Select curated set of fields for downstream use.
4. Write result to a trusted table for reuse by downstream notebooks or reports.
"""

# === Spark Session ===
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
spark = SparkSession.builder.getOrCreate()

# === PARAMETERS ===
trusted_lakehouse_id = "e29a63e5-b594-4b3c-a005-d9dd6019942a"
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"

# === Utility: Path Builder ===
def trusted_path(table_name: str) -> str:
    """
    Constructs the full ABFSS path to a trusted table.
    """
    return f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{trusted_lakehouse_id}/Tables/dbo/salesforce_lcrm_{table_name}_trusted"

# === Load and disambiguate Trusted Tables ===
df_account = (
    spark.read.format("delta").load(trusted_path("account"))
    .withColumnRenamed("id", "ACCT_id")
    .withColumnRenamed("name", "ACCT_account_name")
)

df_member_group = (
    spark.read.format("delta").load(trusted_path("member_group"))
    .withColumnRenamed("id", "MG_id")
    .withColumnRenamed("name", "MG_group_name")
)

# === Join on Account ID ===
df_group_info = df_account.join(
    df_member_group,
    df_account["ACCT_id"] == df_member_group["mg_account_id"],
    how="inner"
)

# === Select curated set of fields ===
selected_fields = [
    "MG_id", "mg_number", "mg_name", "mg_legacy_group_id", "mg_status",
    "ACCT_id", "ACCT_account_name", "friendly_account_name", "guid",
    "admin_line_of_business", "mg_registration_group_code", "client_account_manager",
    "mg_domestic_country", "card_name", "consult_billing_method",
    "mg_primary_eligibility", "mg_dependent_eligibility", "allow_caregiver_program",
    "allow_conversion_to_retail", "mg_allow_geofencing", "allow_minor_registration",
    "one_app_access", "health_assistant", "mg_sexual_health", "teladoc_select",
    "enable_livongo_combined_eligibility", "enable_livongo_referrals",
    "mg_enable_chronic_care_referrals", "livongo_registration_code",
    "livongo_client_code", "mg_mystrength_global_access_code", "cross_billing",
    "mg_direct_mail", "mg_email", "mg_text_sms", "mg_incentives_opt_in",
    "billing_org_id", "print_phone", "print_url"
]

df_group_info = df_group_info.select(*[col(f) for f in selected_fields])

# === Optional: Write to Trusted Output Table ===
output_table_name = "member_group_account_view"

df_group_info.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{trusted_lakehouse_id}/Tables/dbo/salesforce_lcrm_{output_table_name}_trusted")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Transforms the member group + account joined dataset into a long-form (melted) dataset
for per-setting analysis, where each setting becomes a row with its corresponding value,
and field ID is added from the Salesforce-to-admin field mapping table.

Steps:
1. Exclude identifiers (`id`, `legacy_group_id`) from the melt operation.
2. Identify setting columns.
3. Cast all setting columns to string for uniformity.
4. Use Spark's stack() to unpivot settings into key-value format.
5. Join with field mapping table to add field_id.
6. Trim values, deduplicate, and drop null identifiers.
7. Sort for readability and downstream use.
"""

from pyspark.sql import functions as F

# === Step 1: Exclude key ID columns ===
excluded_columns = ["MG_id", "mg_legacy_group_id"]
setting_columns = [col for col in df_group_info.columns if col not in excluded_columns]

# === Step 2: Cast all setting columns to STRING ===
for col_name in setting_columns:
    df_group_info = df_group_info.withColumn(col_name, F.col(col_name).cast("STRING"))

# === Step 3: Construct and apply the stack expression ===
stack_expr = f"stack({len(setting_columns)}, " + ", ".join([f"'{col}', {col}" for col in setting_columns]) + ")"

df_melted = df_group_info.select(
    "MG_id",
    "mg_legacy_group_id",
    F.expr(stack_expr).alias("salesforce_setting_name", "salesforce_setting_value")
)

# === Step 4: Load field mapping table ===
df_field_mappings = spark.read.format("delta").load(trusted_path("to_admin_field_mappings"))

# Select only relevant columns and rename for the join
df_field_mappings = df_field_mappings.select(
    F.col("id").alias("field_id"),
    F.col("salesforce_lcrm_field_name")
)

# === Step 5: Join to bring in field_id ===
df_melted = df_melted.join(
    df_field_mappings,
    df_melted.salesforce_setting_name == df_field_mappings.salesforce_lcrm_field_name,
    how="left"
).drop("salesforce_lcrm_field_name")

# === Step 6: Final cleanup ===
df_melted = (
    df_melted
    .withColumn("salesforce_setting_value", F.trim(F.col("salesforce_setting_value")))
    .dropDuplicates(["MG_id", "mg_legacy_group_id", "salesforce_setting_name", "salesforce_setting_value"])
    .dropna(subset=["MG_id", "mg_legacy_group_id"])
    .orderBy("MG_id", "field_id")
)

# === Display and inspect ===
print(f"Total rows after melting: {df_melted.count()}")
print(df_melted.columns)

# === Step 7: Write the output ===
df_melted.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(trusted_path("member_group_settings_melted"))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
