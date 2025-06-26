# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "5c03804a-6817-4f61-bdd3-d666573c958a",
# META       "default_lakehouse_name": "toast_gab_lh_dev",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "5c03804a-6817-4f61-bdd3-d666573c958a"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Final CSV Tables Creation

# MARKDOWN ********************

# ##### Import required resources

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import array, array_contains, col, concat, current_date, date_sub, expr, last, lit, lower, round, upper, when
from pyspark.sql.types import BooleanType, DateType, DoubleType, IntegerType, StringType, TimestampType
from pyspark.sql.window import Window

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Initialize SparkSession

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

# ### Load Tables

# CELL ********************

raw_gab_member_group_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_member_group_200_silver")

raw_gab_psf_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_plan_specific_fees_200_silver")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Create BenefitSponsorsGroups table

# CELL ********************

# Select only necessary columns from PSF table
gab_psf_df = raw_gab_psf_df.select("member_group_id", "product_end_date", "product_start_date", "admin_payer_id", "bill_to_account_name") # NEW

# Join Member Group and PSF DFs
benefit_sponsor_groups_df = raw_gab_member_group_df.join(gab_psf_df, "member_group_id", "inner")

# Drop unnecessary columns
benefit_sponsor_groups_df = benefit_sponsor_groups_df.drop("member_group_status", "psf_count", "sexual_health", "legacy_group_id", "active_date", "termination_date") # NEW

# Drop duplicate Member Group IDs
benefit_sponsor_groups_df = benefit_sponsor_groups_df.dropDuplicates(["member_group_id"])

# Create a list of columns to replace NULL values with en error message
columns_to_replace_null = [
    "member_group_id", "member_group_name", "card_name", "product_start_date", 
    "primary_eligibility", "cc_dependent_eligibility", "consult_billing_method", 
    "enable_chronic_care_referrals", "enable_livongo_combined_eligibility", 
    "cc_registration_group_code", "one_app_access", "allow_conversion_to_retail", 
    "allow_caregiver_program", "allow_geofencing", "allow_minor_registration",
    "teladoc_select", "health_assistant", "cross_billing", "cc_send_card" # NEW
]

### Replace NULL values with the specified error message
replacement_value = "Please review, this field cannot be NULL!"

for col_name in columns_to_replace_null:
    benefit_sponsor_groups_df = benefit_sponsor_groups_df.withColumn(
        col_name,
        when(col(col_name).isNull(), replacement_value).otherwise(col(col_name))
    )

# Create a list of columns to replace NULL values with an empty string
columns_to_replace_empty = [
    "product_end_date", "livongo_registration_code", 
    "livongo_client_code", "cc_admin_lob", "admin_payer_id", "bill_to_account_name" # NEW
]

### Replace nulls with an empty string
for col_name in columns_to_replace_empty:
    benefit_sponsor_groups_df = benefit_sponsor_groups_df.withColumn(
        col_name,
        when(col(col_name).isNull(), "").otherwise(col(col_name))
    )

# Create cc_payer_id column
benefit_sponsor_groups_df = benefit_sponsor_groups_df.withColumn(
    "cc_payer_id",
    when((col("consult_billing_method") == "Claims") & (col("admin_payer_id") == ""), 483)
    .when((col("consult_billing_method") != "Claims") & (col("admin_payer_id") != ""), "")
    .otherwise(col("admin_payer_id"))
)

# Drop unnecessary columns
benefit_sponsor_groups_df = benefit_sponsor_groups_df.drop("admin_payer_id")

# Replace "rte" with "open" in primary_eligibility and cc_dependent_eligibility
benefit_sponsor_groups_df = benefit_sponsor_groups_df.withColumn("primary_eligibility",
                                                                when(col("primary_eligibility") == "rte", "open")
                                                                .otherwise(col("primary_eligibility")))

benefit_sponsor_groups_df = benefit_sponsor_groups_df.withColumn("cc_dependent_eligibility",
                                                                when(col("cc_dependent_eligibility") == "rte", "open")
                                                                .otherwise(col("cc_dependent_eligibility")))                                                            

# Create new column "Group Information Errors Detected?" to indicate if rows have any errors
error_message = "Please review, this field cannot be NULL!"

benefit_sponsor_groups_df = benefit_sponsor_groups_df.withColumn(
    "group_information_errors_detected",
    when(
        array_contains(
            array(*[col(c).cast("string") for c in benefit_sponsor_groups_df.columns]),
            error_message
        ),
        "Yes"
    ).otherwise("No")
)

# Rename columns
benefit_sponsor_groups_df = benefit_sponsor_groups_df.withColumnsRenamed({"cc_dependent_eligibility": "dependent_eligibility",
                                                                        "cc_registration_group_code": "registration_group_code",
                                                                        "cc_admin_lob": "admin_lob",
                                                                        "product_start_date": "group_start_date",
                                                                        "product_end_date": "group_end_date",
                                                                        "cc_payer_id": "payer_id",
                                                                        "cc_send_card": "send_card"}) # NEW

# Select final columns and ensure correct Data Type
benefit_sponsor_groups_df = benefit_sponsor_groups_df.select(
    col("member_group_id").cast("string"),
    col("member_group_number").cast("string"),
    col("member_group_name").cast("string"),
    col("group_start_date").cast("date"),
    col("group_end_date").cast("date"),
    col("card_name").cast("string"),
    col("primary_eligibility").cast("string"),
    col("dependent_eligibility").cast("string"),
    col("consult_billing_method").cast("string"),
    col("enable_chronic_care_referrals").cast("string"),
    col("livongo_registration_code").cast("string"),
    col("livongo_client_code").cast("string"),
    col("enable_livongo_combined_eligibility").cast("string"),
    col("cross_billing").cast("string"),
    col("registration_group_code").cast("string"),
    col("admin_lob").cast("string"),
    col("one_app_access").cast("string"),
    col("health_assistant").cast("string"),
    col("allow_conversion_to_retail").cast("string"),
    col("allow_caregiver_program").cast("string"),
    col("allow_geofencing").cast("string"),
    col("allow_minor_registration").cast("string"),
    col("teladoc_select").cast("string"),
    col("payer_id").cast("integer"),
    col("account_id").cast("string"),
    col("account_name").cast("string"),
    col("business_region").cast("string"),
    col("group_information_errors_detected").cast("string"),
    col("bill_to_account_name").cast("string"), # NEW
    col("send_card").cast("string"), # NEW
    col("member_group_created_date").cast("timestamp"), # NEW
    col("member_group_last_modified_date").cast("timestamp") # NEW
)

# Sort DF
benefit_sponsor_groups_df = benefit_sponsor_groups_df.orderBy("member_group_name")

# Save table to Lakehouse
if benefit_sponsor_groups_df.isEmpty() == False: # NEW
    benefit_sponsor_groups_df.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/main_csv_gab_dev_benefit_sponsors_groups")

    print("benefit_sponsor_groups_df table saved to Lakehouse successfully!") # NEW

display(benefit_sponsor_groups_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Create Products table

# CELL ********************

# Select only necessary columns from Member Group table
gab_member_group_df = raw_gab_member_group_df.select("member_group_id", "member_group_number", "consult_billing_method")

# Join PSF and Member Group DFs
products_df = raw_gab_psf_df.join(gab_member_group_df, "member_group_id", "inner")

# Create cc_payer_name column
products_df = products_df.withColumn(
    "cc_payer_name",
    when((col("consult_billing_method") == "Claims") & (col("admin_payer_name").isNull()), "Aetna Custom 2024")
    .when((col("consult_billing_method") != "Claims") & (col("admin_payer_name") != ""), "")
    .otherwise(col("admin_payer_name"))
)

# Drop unnecessary columns
products_df = products_df.drop("admin_payer_name", "consult_billing_method", "psf_product_code")

# Create a list of columns to replace NULL values with en error message
columns_to_replace_null = ["cc_product_code", "product_start_date", "fee_type", "cc_final_current_membership_fee", "actual_copay_may_be_less"]

### Replace NULL values with the specified error message
replacement_value = "Please review, this field cannot be NULL!"

for col_name in columns_to_replace_null:
    products_df = products_df.withColumn(
        col_name,
        when(col(col_name).isNull(), replacement_value).otherwise(col(col_name))
    )

### Replace "None" value in fee_type column with the specified error message
products_df = products_df.withColumn("fee_type", when(col("fee_type") == "None", "Please review, this field cannot be NULL!").otherwise(col("fee_type")))

# Create list with columns where NULL should be replaced with an empty string
columns_to_replace_empty = ["product_end_date", "cc_bundle_type", "cc_product_visit_type"]

### Replace NULL values with an empty string
for col_name in columns_to_replace_empty:
    products_df = products_df.withColumn(
        col_name,
        when(col(col_name).isNull(), "").otherwise(col(col_name))
    )

# Create list with columns where NULL should be replaced with a 0
columns_to_replace_zero = ["cc_final_current_membership_fee", "consult_fee_member", "consult_fee_plan", "cc_total_consult_fees"]

### Replace NULL values with 0
for col_name in columns_to_replace_zero:
    products_df = products_df.withColumn(
        col_name,
        when(col(col_name).isNull(), 0).otherwise(col(col_name))
    )

# Create list of Product Codes that MUST have a bundle_type
product_code_list = ["DIAB", "DIABCARE", "DIABP", "DIABPCARE", "HYPT", "HYPTCARE", "MYSTRPLUS", "WEIGM", "WEIGMCARE"]

# Create cc_final_bundle_type column
products_df = products_df.withColumn(
    "cc_final_bundle_type",
    when(
        (col("cc_product_code").isin(product_code_list)) & (col("cc_bundle_type") == ""),
        lit("Please review, this field cannot be NULL!")
    ).otherwise(col("cc_bundle_type"))
)

# Drop unnecessary columns
products_df = products_df.drop("cc_bundle_type")

# Create new column "product_information_errors_detected" to indicate if rows have any errors
error_message = "Please review, this field cannot be NULL!"

products_df = products_df.withColumn(
    "product_information_errors_detected",
    when(
        array_contains(
            array(*[col(c).cast("string") for c in products_df.columns]),
            error_message
        ),
        "Yes"
    ).otherwise("No")
)

# Rename columns
products_df = products_df.withColumnsRenamed({"cc_product_code": "product_code",
                                            "cc_payer_name": "payer_name",
                                            "cc_final_bundle_type": "bundle_type",
                                            "cc_product_visit_type": "product_visit_type",
                                            "cc_total_consult_fees": "consult_fee_total",
                                            "cc_final_current_membership_fee": "membership_fee"})

# Select final columns and ensure correct Data Type
products_df = products_df.select(
    col("member_group_id").cast("string"),
    col("member_group_number").cast("string"),
    col("member_group_name").cast("string"),
    col("psf_id").cast("string"),
    col("psf_number").cast("string"),
    col("product_name").cast("string"),
    col("product_code").cast("string"),
    col("product_visit_type").cast("string"),
    col("product_start_date").cast("date"),
    col("product_end_date").cast("date"),
    col("fee_type").cast("string"),
    col("membership_fee").cast("double"),
    col("consult_fee_member").cast("double"),
    col("consult_fee_plan").cast("double"),
    col("consult_fee_total").cast("double"),
    col("bundle_type").cast("string"),
    col("actual_copay_may_be_less").cast("string"),
    col("usgh_app_opt_out").cast("string"),
    col("glp_1_model").cast("string"),
    col("payer_name").cast("string"),
    col("opportunity_guid").cast("string"),
    col("product_information_errors_detected").cast("string"),
    col("psf_created_date").cast("timestamp"), # NEW
    col("psf_last_modified_date").cast("timestamp") # NEW
)

# Sort DF
products_df = products_df.orderBy("member_group_name")

# Save table to Lakehouse
if products_df.isEmpty() == False: # NEW
    products_df.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/main_csv_gab_dev_products")

    print("products_df table saved to Lakehouse successfully!") # NEW

display(products_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
