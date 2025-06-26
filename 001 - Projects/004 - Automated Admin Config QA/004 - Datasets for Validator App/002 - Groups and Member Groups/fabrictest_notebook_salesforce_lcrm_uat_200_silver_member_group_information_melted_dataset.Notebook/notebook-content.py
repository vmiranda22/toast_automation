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

# # Salesforce LCRM UAT Member Group Information Dataset: Melted & Unmelted

# MARKDOWN ********************

# ##### Import required resources.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, StringType, TimestampType

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Initialize SparkSession.

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

# ##### Load Silver tables.

# CELL ********************

df_salesforce_lcrm_uat_account = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_account")

df_salesforce_lcrm_uat_account_relationship = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_account_relationship")

df_salesforce_lcrm_uat_member_group = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_member_group")

df_salesforce_lcrm_uat_member_group_role = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_member_group_role")

df_salesforce_lcrm_uat_plan_specific_fees_by_product = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_plan_specific_fees_by_product")

df_salesforce_lcrm_uat_subscription = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_subscription")

df_salesforce_lcrm_uat_opportunity = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_opportunity")

df_salesforce_lcrm_uat_product = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_product")

### Objects not needed for now: Asset, Case, Contact, Contract, Opportunity Product, User

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Create Function to add a prefix to columns.

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
    renamed_columns = [F.col(c).alias(f"{prefix}{c}") for c in df.columns]
    
    return df.select(*renamed_columns)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Apply prefix to the columns of each table.

# CELL ********************

df_salesforce_lcrm_uat_account = add_prefix(df_salesforce_lcrm_uat_account, "ACCT_")
df_salesforce_lcrm_uat_account_relationship = add_prefix(df_salesforce_lcrm_uat_account_relationship, "ACCT_REL_")
df_salesforce_lcrm_uat_member_group = add_prefix(df_salesforce_lcrm_uat_member_group, "MG_")
df_salesforce_lcrm_uat_member_group_role = add_prefix(df_salesforce_lcrm_uat_member_group_role, "MGR_")
df_salesforce_lcrm_uat_plan_specific_fees_by_product = add_prefix(df_salesforce_lcrm_uat_plan_specific_fees_by_product, "PSF_")
df_salesforce_lcrm_uat_subscription = add_prefix(df_salesforce_lcrm_uat_subscription, "SUB_")
df_salesforce_lcrm_uat_opportunity = add_prefix(df_salesforce_lcrm_uat_opportunity, "OPP_")
df_salesforce_lcrm_uat_product = add_prefix(df_salesforce_lcrm_uat_product, "PROD_")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Join Account and Member Group Silver tables to get Unmelted Member Group Information **DF FOR COMPARISON WITH ADMIN** (DIFFERENT THAN MG GOLD).

# CELL ********************

salesforce_lcrm_uat_member_group_information_df = df_salesforce_lcrm_uat_account.join(
    df_salesforce_lcrm_uat_member_group,
    df_salesforce_lcrm_uat_account["ACCT_id"] == df_salesforce_lcrm_uat_member_group["MG_account_id"],
    how="inner"
)

# Print row count

row_count = salesforce_lcrm_uat_member_group_information_df.count()

print(f"Total Rows: {row_count}")

# Print unique group_id

unique_count = salesforce_lcrm_uat_member_group_information_df.select("MG_id").distinct().count()

print(f"Unique values in group_id: {unique_count}")

salesforce_lcrm_uat_member_group_information_df = salesforce_lcrm_uat_member_group_information_df.select(
    "MG_id",
    "MG_number",
    "MG_name",
    "MG_legacy_group_id",
    "MG_status",
    "ACCT_id",
    "ACCT_name",
    "ACCT_friendly_account_name",
    "ACCT_guid",
    "MG_admin_line_of_business",
    "MG_registration_group_code",
    "MG_client_account_manager",
    "MG_domestic_country",
    "MG_card_name",
    "MG_consult_billing_method",
    "MG_primary_eligibility",
    "MG_dependent_eligibility",
    "MG_allow_caregiver_program",
    "MG_allow_conversion_to_retail",
    "MG_allow_geofencing",
    "MG_allow_minor_registration",
    "MG_one_app_access",
    "MG_health_assistant",
    "MG_sexual_health",
    "MG_teladoc_select",
    "MG_enable_livongo_combined_eligibility",
    "MG_enable_livongo_referrals",
    "MG_enable_chronic_care_referrals",
    "MG_livongo_registration_code",
    "MG_livongo_client_code",
    "MG_mystrength_global_access_code",
    "MG_cross_billing",
    "MG_direct_mail",
    "MG_email",
    "MG_text_sms",
    "MG_incentives_opt_in",
    "ACCT_billing_org_id",
    "ACCT_print_phone",
    "ACCT_print_url"
)

salesforce_lcrm_uat_member_group_information_df = salesforce_lcrm_uat_member_group_information_df.orderBy("MG_legacy_group_id")

display(salesforce_lcrm_uat_member_group_information_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

salesforce_lcrm_uat_member_group_information_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_member_group_information")
    
print("✅ Dataset saved!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Create the **MELTED** dataset with Member Group Settings data.

# CELL ********************

# Most of these columns shouldn't have to be excluded because they shouldn't be brought in. Filters need to be applied to these columns when reading the tables.
excluded_columns = ["MG_id", "MG_legacy_group_id"]

# Identify the columns to be included as "settings" (exclude g_group_id)
setting_columns = [col for col in salesforce_lcrm_uat_member_group_information_df.columns if col not in excluded_columns]

# Cast all setting columns to STRING (better than selectExpr)
for col_name in setting_columns:
    salesforce_lcrm_uat_member_group_information_df = salesforce_lcrm_uat_member_group_information_df.withColumn(col_name, F.col(col_name).cast("STRING"))

# Construct the stack expression correctly
stack_expr = "stack({}, {})".format(
    len(setting_columns), 
    ", ".join([f"'{col}', {col}" for col in setting_columns])
)

salesforce_lcrm_uat_member_group_information_df_melted = salesforce_lcrm_uat_member_group_information_df.select(
    *[F.col(c) for c in ["MG_id", "MG_legacy_group_id"]],
    F.expr(stack_expr).alias("salesforce_setting_name", "salesforce_setting_value")
)

# Trim & deduplicate data
salesforce_lcrm_uat_member_group_information_df_melted = salesforce_lcrm_uat_member_group_information_df_melted.withColumn("salesforce_setting_value", F.trim(F.col("salesforce_setting_value"))).dropDuplicates(["MG_id", "MG_legacy_group_id", "salesforce_setting_name", "salesforce_setting_value"])
salesforce_lcrm_uat_member_group_information_df_melted = salesforce_lcrm_uat_member_group_information_df_melted.orderBy("MG_id")

# Drop rows that have NULL values in MG_id and MG_legacy_group_id columns
salesforce_lcrm_uat_member_group_information_df_melted = salesforce_lcrm_uat_member_group_information_df_melted.dropna(subset=["MG_id"])
salesforce_lcrm_uat_member_group_information_df_melted = salesforce_lcrm_uat_member_group_information_df_melted.dropna(subset=["MG_legacy_group_id"])

# Delete MG_legacy_group_id rows that are NULL

print(f"Total rows after melting: {salesforce_lcrm_uat_member_group_information_df_melted.count()}")
print(salesforce_lcrm_uat_member_group_information_df_melted.columns)

display(salesforce_lcrm_uat_member_group_information_df_melted)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Save **MELTED** dataset.

# CELL ********************

salesforce_lcrm_uat_member_group_information_df_melted.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save(f"abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_member_group_information_melted")

print("✅ Dataset saved!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Check if there are multiple Member Group IDs for a single Legacy Group ID.

# CELL ********************

# Assuming df is your existing DataFrame
df_melted_qa = salesforce_lcrm_uat_member_group_information_df_melted.groupBy("MG_legacy_group_id").agg(F.countDistinct("MG_id").alias("unique_mg_id_count"))

# Filter groups that have more than one unique MG_id
invalid_groups = df_melted_qa.filter(df_melted_qa["unique_mg_id_count"] > 1)

# Show results
if invalid_groups.count() == 0:
    print("Each MG_legacy_group_id has only one MG_id.")
else:
    print("These MG_legacy_group_id values have multiple MG_id values:")
    invalid_groups.show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Join Account & Account Relationship tables to get Unmelted Account Information DF.

# MARKDOWN ********************

# salesforce_lcrm_uat_account_information_df = df_salesforce_lcrm_uat_account.join(
#     df_salesforce_lcrm_uat_account_relationship,
#     df_salesforce_lcrm_uat_account["ACCT_id"] == df_salesforce_lcrm_uat_account_relationship["ACCT_REL_benefit_sponsor_id"],
#     how="left_outer"
# )
# 
# display(salesforce_lcrm_uat_account_information_df)
# 
#  Print row count
# 
# row_count = salesforce_lcrm_uat_account_information_df.count()
# 
# print(f"Total Rows: {row_count}")
# 
#  Print unique group_id
# 
# unique_count = salesforce_lcrm_uat_account_information_df.select("ACCT_id").distinct().count()
# 
# print(f"Unique values in group_id: {unique_count}")

# MARKDOWN ********************

# salesforce_lcrm_uat_account_information_df.write.format("delta") \
#     .option("overwriteSchema", "true") \
#     .mode("overwrite") \
#     .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_300_gold_account_information")
#     
# print("✅ Dataset saved!")

# MARKDOWN ********************

# salesforce_lcrm_uat_products_information_df = df_salesforce_lcrm_uat_plan_specific_fees_by_product.join(
#     df_salesforce_lcrm_uat_subscription,
#     df_salesforce_lcrm_uat_plan_specific_fees_by_product["PSF_subscription_id"] == df_salesforce_lcrm_uat_subscription["SUB_id"],
#     how="left_outer"
# )
# 
# salesforce_lcrm_uat_products_information_df = salesforce_lcrm_uat_products_information_df.join(
#     df_salesforce_lcrm_uat_opportunity,
#     salesforce_lcrm_uat_products_information_df["SUB_opportunity_id"] == df_salesforce_lcrm_uat_opportunity["OPP_id"],
#     how="left_outer"
# )
# 
# salesforce_lcrm_uat_products_information_df = salesforce_lcrm_uat_products_information_df.join(
#     df_salesforce_lcrm_uat_product,
#     salesforce_lcrm_uat_products_information_df["SUB_product_id"] == df_salesforce_lcrm_uat_product["PROD_id"],
#     how="left_outer"
# )
# 
# salesforce_lcrm_uat_products_information_df = salesforce_lcrm_uat_products_information_df.orderBy("PSF_member_group_id", "PSF_name", "PSF_product", "PSF_asset_name")
# 
# display(salesforce_lcrm_uat_products_information_df)


# MARKDOWN ********************

# salesforce_lcrm_uat_products_information_df.write.format("delta") \
#     .option("overwriteSchema", "true") \
#     .mode("overwrite") \
#     .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_300_gold_products_information")
#     
# print("✅ Dataset saved!")

# MARKDOWN ********************

# Join all objects to get a full DF.

# MARKDOWN ********************

# df_salesforce_lcrm_uat = df_salesforce_lcrm_uat_account.join(
#     df_salesforce_lcrm_uat_account_relationship,
#     df_salesforce_lcrm_uat_account["ACCT_id"] == df_salesforce_lcrm_uat_account_relationship["ACCT_REL_benefit_sponsor_id"],
#     how="left_outer"
# )
# 
# df_salesforce_lcrm_uat = df_salesforce_lcrm_uat.join(
#     df_salesforce_lcrm_uat_member_group,
#     df_salesforce_lcrm_uat["ACCT_id"] == df_salesforce_lcrm_uat_member_group["MG_account_id"],
#     how="left_outer"
# )
# 
# df_salesforce_lcrm_uat = df_salesforce_lcrm_uat.join(
#     df_salesforce_lcrm_uat_member_group_role,
#     df_salesforce_lcrm_uat["MG_id"] == df_salesforce_lcrm_uat_member_group_role["MGR_member_group_id"],
#     how="left_outer"
# )
# 
# df_salesforce_lcrm_uat = df_salesforce_lcrm_uat.join(
#     df_salesforce_lcrm_uat_plan_specific_fees_by_product,
#     df_salesforce_lcrm_uat["MG_id"] == df_salesforce_lcrm_uat_plan_specific_fees_by_product["PSF_member_group_id"],
#     how="left_outer"
# )
# 
# df_salesforce_lcrm_uat = df_salesforce_lcrm_uat.join(
#     df_salesforce_lcrm_uat_subscription,
#     df_salesforce_lcrm_uat["PSF_subscription_id"] == df_salesforce_lcrm_uat_subscription["SUB_id"],
#     how="left_outer"
# )
# 
# df_salesforce_lcrm_uat = df_salesforce_lcrm_uat.join(
#     df_salesforce_lcrm_uat_opportunity,
#     df_salesforce_lcrm_uat["SUB_opportunity_id"] == df_salesforce_lcrm_uat_opportunity["OPP_id"],
#     how="left_outer"
# )
# 
# df_salesforce_lcrm_uat = df_salesforce_lcrm_uat.join(
#     df_salesforce_lcrm_uat_product,
#     df_salesforce_lcrm_uat["SUB_product_id"] == df_salesforce_lcrm_uat_product["PROD_id"],
#     how="left_outer"
# )
# 
# df_salesforce_lcrm_uat.orderBy(["MG_legacy_group_id"])
# 
# display(df_salesforce_lcrm_uat)

