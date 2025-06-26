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

# # Comparison Dataset (Salesforce LCRM vs. Admin EDS) - Group Settings

# MARKDOWN ********************

# ##### Import required resources.

# CELL ********************

import time
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

# ##### Load Salesforce LCRM and Admin EDS Silver Melted Datasets.

# CELL ********************

df_melted_salesforce_uat_group_settings = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_200_silver_member_group_information_melted")

df_melted_admin_eds_group_settings = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_group_information_melted")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_melted_salesforce_uat_group_settings_filtered = df_melted_salesforce_uat_group_settings.filter(df_melted_salesforce_uat_group_settings.MG_legacy_group_id == 575083)

display(df_melted_salesforce_uat_group_settings_filtered)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_melted_admin_eds_group_settings_filtered = df_melted_admin_eds_group_settings.filter(df_melted_admin_eds_group_settings.legacy_group_id == 575083)

display(df_melted_admin_eds_group_settings_filtered)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Perform an inner join to find matching values
# matching_df = melted_df.alias("df1").join(
#     df_eds_group_settings.alias("df2"),
#     col("df1.MG_legacy_group_id") == col("df2.g_legacy_group_id"),
#     "inner"
# )
# 
# # Get the first matching value
# first_match = matching_df.select("df1.MG_legacy_group_id").limit(1).collect()
# 
# # Check if there's a match and print the result
# if first_match:
#     print(f"First matching value found: {first_match[0][0]}")
# else:
#     print("No matching values found.")


# CELL ********************

# Start time
start_time = time.time()

# Mapping dictionary for setting names
settings_mapping = {
    "MG_admin_line_of_business": "lob_cd",
    # "MG_allow_caregiver_program": MISSING IN ADMIN,
    "MG_allow_conversion_to_retail": "allow_conversion_to_retail",
    "MG_allow_geofencing": "enable_geo_fencing",
    "MG_allow_minor_registration": "minor_registration",
    "MG_card_name": "card_nm",
    # "MG_client_account_manager": "account_manager",
    "MG_consult_billing_method": "consult_reimbursement_method_cd",
    "MG_cross_billing": "cross_billing",
    "MG_dependent_eligibility": "dependent_source_cd",
    "MG_domestic_country": "country_nm",
    "MG_enable_chronic_care_referrals": "enable_chronic_care_referrals",
    "MG_enable_livongo_combined_eligibility": "livongo_combined_eligibility",
    # "MG_status": "group_status",
    "MG_health_assistant": "allow_health_assistant",
    "MG_livongo_client_code": "livongo_client_code",
    "MG_livongo_registration_code": "livongo_registration_code",
    "MG_mystrength_global_access_code": "mystrength_global_access_code",
    "MG_name": "group_nm",
    "MG_one_app_access": "one_app_access",
    "MG_primary_eligibility": "primary_source_cd",
    "MG_registration_group_code": "registration_group_cd",
    "MG_direct_mail": "direct_mail",
    "MG_email": "email",
    "MG_text_sms": "sms_text",
    "MG_incentives_opt_in": "incentive",
    "ACCT_print_phone": "print_phone",
    "ACCT_print_url": "print_url",
    "ACC_": "web_url"
}

# Convert mapping dictionary into a DataFrame for easy joining
mapping_df = spark.createDataFrame([(k, v) for k, v in settings_mapping.items()], ["salesforce_setting_name", "admin_setting_name"])

# Join salesforce dataset with the mapping table
salesforce_mapped_df = df_melted_salesforce_uat_group_settings.join(mapping_df, "salesforce_setting_name", "left")

# Join the mapped Salesforce dataset with the admin dataset on the mapped setting name and legacy group ID
final_df = (
    salesforce_mapped_df
    .join(
        df_melted_admin_eds_group_settings,
        (salesforce_mapped_df.MG_legacy_group_id == df_melted_admin_eds_group_settings.legacy_group_id) &
        (salesforce_mapped_df.admin_setting_name == df_melted_admin_eds_group_settings.admin_setting_name), 
        "inner"
    )
    .select(
        salesforce_mapped_df.MG_id,
        df_melted_admin_eds_group_settings.group_id,
        df_melted_admin_eds_group_settings.legacy_group_id,
        salesforce_mapped_df.salesforce_setting_name,
        salesforce_mapped_df.salesforce_setting_value,
        df_melted_admin_eds_group_settings.admin_setting_name,
        df_melted_admin_eds_group_settings.admin_setting_value,
        F.when(
            (salesforce_mapped_df.salesforce_setting_value == df_melted_admin_eds_group_settings.admin_setting_value) |
            (salesforce_mapped_df.salesforce_setting_value.isNull() & df_melted_admin_eds_group_settings.admin_setting_value.isNull()), 
            "MATCH"
        ).otherwise("NO MATCH").alias("does_value_match")
    )
)

final_df = final_df.orderBy(F.col("group_id").desc(), F.col("salesforce_setting_name").asc())

# Count total rows
row_count = final_df.count()

# End time
end_time = time.time()
execution_time = end_time - start_time

# Print results
print(f"Total rows processed: {row_count}")
print(f"Total execution time: {execution_time:.2f} seconds")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(final_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

display(final_df.filter(final_df.legacy_group_id == 575083))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

final_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/comparison_dataset_melted_group_settings")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
