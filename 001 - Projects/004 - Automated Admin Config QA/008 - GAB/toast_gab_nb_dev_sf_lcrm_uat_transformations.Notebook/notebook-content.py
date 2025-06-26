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

# # Salesforce Tables Transformations

# MARKDOWN ********************

# ##### Import required resources

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, current_date, date_sub, expr, last, lit, lower, round, upper, when
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

raw_account_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_account_100_bronze")

raw_member_group_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_member_group_100_bronze")

raw_opportunity_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_opportunity_100_bronze")

raw_psf_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_plan_specific_fees_100_bronze")

raw_subscription_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_subscription_100_bronze")

raw_payers_excel_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sp_excel_gab_admin_payers_to_salesforce")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Set the number of days to filter the objects later on

# CELL ********************

last_days = 90

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Transform Account

# CELL ********************

# Rename columns
gab_account_df = raw_account_df.withColumnsRenamed({
    "Id": "account_id",
    "Name": "account_name",
    "Billing_Org_ID__c": "billing_org_id",
    "Business_Region__c": "business_region",
    "Friendly_Account_Name__c": "account_friendly_name",
    "GUID__c": "account_guid",
    "CreatedDate": "account_created_date",
    "LastModifiedDate": "account_last_modified_date"
    })

# Sort table
gab_account_df = gab_account_df.orderBy("account_last_modified_date", asc=[False])

# Save table to Lakehouse
if gab_account_df.isEmpty() == False:
    gab_account_df.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_account_200_silver")
        
    print("gab_account_df table saved to Lakehouse successfully!")

display(gab_account_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Transform Member Group

# CELL ********************

# Filter rows where LastModifiedDate is today or within the last last_days AND Status__c is PENDING

gab_member_group_df = raw_member_group_df.filter(
    (col("Status__c") == "PENDING") &
    ((col("LastModifiedDate") >= date_sub(current_date(), last_days)) | (col("LastModifiedDate") == current_date())) &
    (col("Group_Number__c").isNull())
)

# Lowercase the Eligibility_Option__c column
gab_member_group_df = gab_member_group_df.withColumn("Eligibility_Option__c", lower(col("Eligibility_Option__c")))

# Replace specific values in Eligibility_Option__c
gab_member_group_df = gab_member_group_df.withColumn("Eligibility_Option__c",
                                                    when(col("Eligibility_Option__c") == "staged eligibility & rte", "hybrid")
                                                    .when(col("Eligibility_Option__c") == "api(staged eligibility & open)", "api")
                                                    .otherwise(col("Eligibility_Option__c")))

# Replace specific values in Consult_Billing_Method__c
gab_member_group_df = gab_member_group_df.withColumn("Consult_Billing_Method__c",
                                                    when(col("Consult_Billing_Method__c") == "N/A", "Not Applicable (Consults Included)")
                                                    .otherwise(col("Consult_Billing_Method__c")))

# Replace NULL values with an empty string and replace MyStrength Global in Enable_Chronic_Care_Referrals__c
gab_member_group_df = gab_member_group_df.fillna({"Enable_Chronic_Care_Referrals__c": ""})

### CLIENT PORTAL DOES NOT ACCEPT "myStrength Global" as a valid value, so I'm changing it to blank
gab_member_group_df = gab_member_group_df.withColumn("Enable_Chronic_Care_Referrals__c",
                                                    when(col("Enable_Chronic_Care_Referrals__c") == "MyStrength Global", "")
                                                    .otherwise(col("Enable_Chronic_Care_Referrals__c")))

# List of columns to replace boolean string values with 'Y' or 'N'
boolean_columns = [
    "Allow_Caregiver_Program__c", "Allow_Conversion_to_Retail__c", "Allow_Geo_Fencing__c", "Allow_Minor_Registration__c", "Health_Assistant__c",
    "OneAppAccess__c", "Enable_Livongo_Combined_Eligibility__c", "Sexual_Health_Opt_Out__c", "Teladoc_Select__c", "Cross_Billing__c"
]

### Apply the boolean string replacement
for column in boolean_columns:
    gab_member_group_df = gab_member_group_df.withColumn(
        column,
        when((col(column) == "True") | (col(column) == "Yes"), "Y")
        .when((col(column) == "False") | (col(column) == "No"), "N")
        .otherwise(col(column))
    )

# Create cc_dependent_eligibility column based on Elig_Dep_Inc_In_File__c
gab_member_group_df = gab_member_group_df.withColumn("cc_dependent_eligibility",
                                                    when(col("Elig_Dep_Inc_In_File__c") == "True", col("Eligibility_Option__c"))
                                                    .otherwise(lit("open")))

# Create cc_registration_group_code column concatenating "SF2Admin_" with the Member Group ID
gab_member_group_df = gab_member_group_df.withColumn("cc_registration_group_code", concat(lit("SF2Admin_"), col("Id")))

# Map Admin LOB values to their corresponding LOBTYPE codes
lob_mapping = {
    "Commercial ASO": "LOBTYPE_ASO",
    "Children's Health Insurance Program (CHIP)": "LOBTYPE_CHIP",
    "Dual Eligible Special Needs Plans (DSNP)": "LOBTYPE_DSNP",
    "Commercial FI": "LOBTYPE_FI",
    "Medicare Advantage Part D (MAPD)": "LOBTYPE_MAPD",
    "Marketplace": "LOBTYPE_MARKETPLACE",
    "Medicaid Managed Care": "LOBTYPE_MEDICAID",
    "Medicaid FFS": "LOBTYPE_MEDICAIDFFS",
    "Medicaid Supplement": "LOBTYPE_MEDICAIDSUP",
    "Medicare Advantage": "LOBTYPE_MEDICARE",
    "Medicare FFS": "LOBTYPE_MEDICAREFFS",
    "Medicare-Medicaid Plan (MMP)": "LOBTYPE_MMPDUAL",
    "LOBTYPE_NOTKNOWN": "LOBTYPE_NOTKNOWN",
    "Temporary Assistance for Needy Families (TANF)": "LOBTYPE_TANF"
}

### Apply Admin LOB mapping
cc_admin_lob_col = None

for key, value in lob_mapping.items():
    condition = col("Admin_Line_of_Business__c") == key
    cc_admin_lob_col = when(condition, value) if cc_admin_lob_col is None else cc_admin_lob_col.when(condition, value)

### Create cc_admin_lob column
gab_member_group_df = gab_member_group_df.withColumn("cc_admin_lob", cc_admin_lob_col.otherwise(None))

# Create cc_send_card column based on Card_Template__c # NEW
gab_member_group_df = gab_member_group_df.withColumn("cc_send_card",
                                                    when(col("Card_Template__c") == "Logo Card", lit("Y"))
                                                    .when(col("Card_Template__c") == "STND Card", lit("Y"))
                                                    .otherwise(lit("N")))

# Uppercase the Livongo_Registration_code__c and LV_Client_Code__c columns
gab_member_group_df = gab_member_group_df.withColumn("Livongo_Registration_code__c", upper(col("Livongo_Registration_code__c")))

gab_member_group_df = gab_member_group_df.withColumn("LV_Client_Code__c", upper(col("LV_Client_Code__c")))

# Drop unnecessary columns
gab_member_group_df = gab_member_group_df.drop("Admin_Line_of_Business__c", "Elig_Dep_Inc_In_File__c", "Migration_Group_Number__c")

# Rename columns
gab_member_group_df = gab_member_group_df.withColumnsRenamed({
    "Id": "member_group_id",
    "Name": "member_group_number",
    "CreatedDate": "member_group_created_date",
    "LastModifiedDate": "member_group_last_modified_date",
    "Client_Account__c": "account_id",
    "Allow_Caregiver_Program__c": "allow_caregiver_program",
    "Allow_Conversion_to_Retail__c": "allow_conversion_to_retail",
    "Allow_Geo_Fencing__c": "allow_geofencing",
    "Card_Name__c": "card_name",
    "Consult_Billing_Method__c": "consult_billing_method",
    "Eligibility_Option__c": "primary_eligibility",
    "Name__c": "member_group_name",
    "Sexual_Health_Opt_Out__c": "sexual_health",
    "Status__c": "member_group_status",
    "Teladoc_Select__c": "teladoc_select",
    "PSF_Count__c": "psf_count",
    "Health_Assistant__c": "health_assistant",
    "Enable_Livongo_Combined_Eligibility__c": "enable_livongo_combined_eligibility",
    "Livongo_Registration_code__c": "livongo_registration_code",
    "Enable_Chronic_Care_Referrals__c": "enable_chronic_care_referrals",
    "MyStrength_Global_Access_Code__c": "mystrength_global_access_code",
    "Cross_Billing__c": "cross_billing",
    "Allow_Minor_Registration__c": "allow_minor_registration",
    "OneAppAccess__c": "one_app_access",
    "LV_Client_Code__c": "livongo_client_code",
    "Card_Template__c": "card_template", # NEW
    "Group_Number__c": "legacy_group_id", # NEW
    "Active_Date__c": "active_date", # NEW
    "Termination_Date__c": "termination_date" # NEW
    })

# Merge Member Group with Account to obtain Business Region
gab_member_group_df = gab_member_group_df.join(gab_account_df.select("account_id", "account_name", "business_region"), "account_id", "inner")

# Sort table
gab_member_group_df = gab_member_group_df.orderBy("member_group_last_modified_date", asc=[False])

# Save table to Lakehouse
if gab_member_group_df.isEmpty() == False:
    gab_member_group_df.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_member_group_200_silver")

    print("gab_member_group_df table saved to Lakehouse successfully!")

display(gab_member_group_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Transform Opportunity

# CELL ********************

# Remove last 3 characters from Id column
gab_opportunity_df = raw_opportunity_df.withColumn("Id", expr("substring(Id, 1, 15)"))

# Rename columns
gab_opportunity_df = gab_opportunity_df.withColumnsRenamed({
    "Id": "opportunity_id",
    "Name": "opportunity_name",
    "Opp_Guid__c": "opportunity_guid",
    "AccountId": "account_id",
    "CreatedDate": "opportunity_created_date",
    "LastModifiedDate": "opportunity_last_modified_date"
    })

# Sort table
gab_opportunity_df = gab_opportunity_df.orderBy("opportunity_last_modified_date", asc=[False])

# Save table to Lakehouse
if gab_opportunity_df.isEmpty() == False:
    gab_opportunity_df.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_opportunity_200_silver")

    print("gab_opportunity_df table saved to Lakehouse successfully!")

display(gab_opportunity_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Transform Subscription

# CELL ********************

# Replace values in Bundle_Type__c column
gab_subscription_df = raw_subscription_df.withColumn(
    "cc_bundle_type",
    when(col("Bundle_Type__c") == "Anchor", "BUNDLETYPE_WPANCHOR")
    .when(col("Bundle_Type__c") == "Non-Anchor", "BUNDLETYPE_WPNONANCHOR")
    .when(col("Bundle_Type__c") == "Standalone", "BUNDLETYPE_STANDALONE")
    .otherwise(lit(""))
)

# Drop unnnecessary columns
gab_subscription_df = gab_subscription_df.drop("Bundle_Type__c")

# Round Current_Membership_Fee__c
gab_subscription_df = gab_subscription_df.withColumn("Current_Membership_Fee__c", round(col("Current_Membership_Fee__c"), 2))

# Rename columns
gab_subscription_df = gab_subscription_df.withColumnsRenamed({
    "Id": "subscription_id",
    "Name": "subscription_number",
    "CurrencyIsoCode": "currency_iso_code",
    "SBQQ__Account__c": "account_id",
    "SBQQ__ProductName__c": "product_name",
    "Current_Membership_Fee__c": "current_membership_fee",
    "Fee_Type__c": "fee_type",
    "Oportunity_Id__c": "opportunity_id",
    "Status__c": "subscription_status",
    "CreatedDate": "subscription_created_date",
    "LastModifiedDate": "subscription_last_modified_date"
})

# Join with Opportunity table to get Opportunity GUID
gab_subscription_df = gab_subscription_df.join(gab_opportunity_df.select("opportunity_id", "opportunity_guid"), "opportunity_id", "left_outer")

# Sort table
gab_subscription_df = gab_subscription_df.orderBy("subscription_last_modified_date", asc=[False])

# Save table to Lakehouse
if gab_subscription_df.isEmpty() == False:
    gab_subscription_df.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_subscription_200_silver")

    print("gab_subscription_df table saved to Lakehouse successfully!")

display(gab_subscription_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Transform Plan-Specific Fees

# MARKDOWN ********************

# ##### PSF - Main

# CELL ********************

# Filter rows where LastModifiedDate is today OR within the last last_days AND Status is PENDING
gab_psf_df = raw_psf_df.filter(
    (col("Product_End_Date__c").isNull()) & ((col("LastModifiedDate") >= date_sub(current_date(), last_days)) | (col("LastModifiedDate") == current_date()))
)

# Create list with unique Member Group IDs in Member Group table
member_group_ids_list = gab_member_group_df.select("member_group_id").distinct().rdd.flatMap(lambda x: x).collect()

# Filter PSF DF to keep only the Member Group IDs in Member Group table
gab_psf_df = gab_psf_df.filter(col("Member_Group__c").isin(member_group_ids_list))

# Join with Member Group to get Business Region
gab_psf_df = gab_psf_df.join(gab_member_group_df.select("member_group_id", "business_region"), col("Member_Group__c") == col("member_group_id"), "inner")

# Drop unnecessary columns
gab_psf_df = gab_psf_df.drop("member_group_id")

# Cast Product Start Date and Product End Date to Timestamp
gab_psf_df = gab_psf_df.withColumn("Product_Start_Date__c", col("Product_Start_Date__c").cast(TimestampType()))
gab_psf_df = gab_psf_df.withColumn("Product_End_Date__c", col("Product_End_Date__c").cast(TimestampType()))

# Round Consult Fee columns
gab_psf_df = gab_psf_df.withColumn("Consult_Fee_Mbr_Pd__c", round(col("Consult_Fee_Mbr_Pd__c"), 2))
gab_psf_df = gab_psf_df.withColumn("Consult_Fee_Plan_Pd__c", round(col("Consult_Fee_Plan_Pd__c"), 2))

# Rename columns
gab_psf_df = gab_psf_df.withColumnRenamed("Subscription__c", "subscription_id")

# Join PSF with Subscription table
gab_psf_df = gab_psf_df.join(gab_subscription_df.select("subscription_id", "current_membership_fee", "fee_type", "cc_bundle_type", "opportunity_guid"),
                            "subscription_id",
                            "inner")

display(gab_psf_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### PSF - BH for MYSTR3 & EFAP

# CELL ********************

# Create DF with only Mental Health Complete OR EFAP rows 
psf_bh_df = gab_psf_df.filter((col("Product__c") == "Mental Health Complete") | (col("PSF_ProductCode__c") == "EFAP"))

# Replace values in Product__c column
psf_bh_df = psf_bh_df.withColumn("Product__c", lit("Mental Health Care (US)"))

# Set current_membership_fee column to 0
psf_bh_df = psf_bh_df.withColumn("current_membership_fee", col("current_membership_fee") * 0)

# Replace values in Asset_Name__c column
psf_bh_df = psf_bh_df.withColumn("Asset_Name__c",
                                when(col("Asset_Name__c").isNull(), lit("Therapy Ongoing Visit Fee"))
                                .otherwise(col("Asset_Name__c")))

display(psf_bh_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### PSF - Pathology for BH 

# CELL ********************

# Create DF with only Psychiatry Initial Visit Fee OR MYS - MyStrength Global rows 
psf_pathology_df = gab_psf_df.filter((col("Asset_Name__c") == "Psychiatry Initial Visit Fee") | (col("Product__c") == "MYS - MyStrength Global"))

# Set pathology for Product__c and Asset_Name__c columns
psf_pathology_df = psf_pathology_df.withColumn("Asset_Name__c", lit("pathology"))
psf_pathology_df = psf_pathology_df.withColumn("Product__c", lit("pathology"))

# Set Fees columns to 0
psf_pathology_df = psf_pathology_df.withColumn("current_membership_fee", col("current_membership_fee") * 0)
psf_pathology_df = psf_pathology_df.withColumn("Consult_Fee_Mbr_Pd__c", col("Consult_Fee_Mbr_Pd__c") * 0)
psf_pathology_df = psf_pathology_df.withColumn("Consult_Fee_Plan_Pd__c", col("Consult_Fee_Plan_Pd__c") * 0)

# Replace values in Actual_Copay_May_Be_Less__c column
psf_pathology_df = psf_pathology_df.withColumn("Actual_Copay_May_Be_Less__c",
                                when(col("Actual_Copay_May_Be_Less__c") == "True", lit("False"))
                                .otherwise(col("Actual_Copay_May_Be_Less__c")))

display(psf_pathology_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### PSF - MSGLOBAL for EFAP

# CELL ********************

# Create DF with only EFAP rows 
psf_msglobal_df = gab_psf_df.filter(col("PSF_ProductCode__c") == "EFAP")

# Replace values in Product__c column
psf_msglobal_df = psf_msglobal_df.withColumn("Product__c",
                                when(col("Product__c") == "Mental Health Complete", lit("Mental Health Care (US)"))
                                .when(col("Product__c") == "Employee and Family Assistance Program", lit("MYS - MyStrength Global"))
                                .otherwise(col("Product__c")))

# Set current_membership_fee column to 0
psf_msglobal_df = psf_msglobal_df.withColumn("current_membership_fee", col("current_membership_fee") * 0)

# Replace values in Actual_Copay_May_Be_Less__c column
psf_msglobal_df = psf_msglobal_df.withColumn("Actual_Copay_May_Be_Less__c",
                                when(col("Actual_Copay_May_Be_Less__c") == "True", lit("False"))
                                .otherwise(col("Actual_Copay_May_Be_Less__c")))

# Replace values in cc_bundle_type column
psf_msglobal_df = psf_msglobal_df.withColumn("cc_bundle_type",
                                when(col("cc_bundle_type") == "", lit("BUNDLETYPE_STANDALONE"))
                                .otherwise(col("cc_bundle_type")))

display(psf_msglobal_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### PSF - Mental Health Care (Canada)

# CELL ********************

# Create DF with only EFAP rows 
psf_mhcanada_df = gab_psf_df.filter(col("Product__c") == "Mental Health Care (Canada)")

# Drop rows where Asset_Name__c contains "Psychiatry"
psf_mhcanada_df = psf_mhcanada_df.filter(~(col("Asset_Name__c").contains("Psychiatry")))

# Replace values in Product__c column
psf_mhcanada_df = psf_mhcanada_df.withColumn("Product__c", lit("Mental Health Care (US)"))

display(psf_mhcanada_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### PSF - Sexual Health

# CELL ********************

# Join PSF with Member Group table to get Sexual Health field
psf_sh_df = gab_psf_df.join(gab_member_group_df.select("member_group_id", "sexual_health"), col("Member_Group__c") == col("member_group_id"), "inner")

# Filter DF to keep only Member Groups that have Sexual Health
psf_sh_df = psf_sh_df.filter((col("sexual_health") == "Y") & (col("Product__c") == "General Medical"))

# Drop unnecessary columns
psf_sh_df = psf_sh_df.drop("member_group_id", "sexual_health")

# Drop Member_Group__C duplicates
psf_sh_df = psf_sh_df.dropDuplicates(["Member_Group__C"])

# Replace values in Product__c column
psf_sh_df = psf_sh_df.withColumn("Product__c", lit("Sexual Health"))

# Replace values in Asset_Name__c column
psf_sh_df = psf_sh_df.withColumn("Asset_Name__c", lit(""))

# Set Fees columns to 0
psf_sh_df = psf_sh_df.withColumn("current_membership_fee", col("current_membership_fee") * 0)
psf_sh_df = psf_sh_df.withColumn("Consult_Fee_Mbr_Pd__c", col("Consult_Fee_Mbr_Pd__c") * 0)
psf_sh_df = psf_sh_df.withColumn("Consult_Fee_Plan_Pd__c", col("Consult_Fee_Plan_Pd__c") * 0)

# Replace values in Actual_Copay_May_Be_Less__c column
psf_sh_df = psf_sh_df.withColumn("Actual_Copay_May_Be_Less__c",
                                when(col("Actual_Copay_May_Be_Less__c") == "True", lit("False"))
                                .otherwise(col("Actual_Copay_May_Be_Less__c")))

display(psf_sh_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Union PSFs

# CELL ********************

# Union all PSFs DFs
gab_psf_df_final = gab_psf_df.unionByName(psf_bh_df).unionByName(psf_pathology_df).unionByName(psf_msglobal_df).unionByName(psf_mhcanada_df).unionByName(psf_sh_df)

# Replace NULL values in Asset_Name__c with empty string
gab_psf_df_final = gab_psf_df_final.withColumn("Asset_Name__c",
                                                when(col("Asset_Name__c").isNull(), "")
                                                .otherwise(col("Asset_Name__c")))

# Replace values in Actual_Copay_May_Be_Less__c column
gab_psf_df_final = gab_psf_df_final.withColumn("Actual_Copay_May_Be_Less__c",
                                                when(col("Actual_Copay_May_Be_Less__c") == "True", lit("Y"))
                                                .when(col("Actual_Copay_May_Be_Less__c") == "False", lit("N"))
                                                .otherwise(col("Actual_Copay_May_Be_Less__c")))

# Map Product names from Product__c column to their corresponding Product Code required by Client Portal
product_mapping = {
    "Advanced Prediabetes": "ADVNCDIABETESPRVNTNPRGRM",
    "Advanced Weight Management (Select Populations)": "ADVANCEWEIGHTMANAGEMENT",
    "Analytics (Stratus) Standalone": "ASTRAT",
    "Analytics with Consulting": "ACON",
    "Analytics with Targeted Outreach": "TOE",
    "Ask the Expert 2.0": "AAD",
    "Ask the Expert": "ATE",
    "Back and Joint Support": "TDBC",
    "BD - Core Bundle (CANADA)": "BD-CANADA-BUNDLE",
    "BD - Core Bundle (US Employer)": "BD-USEMP-BUNDLE",
    "BD - Core Bundle 2.0 (CANADA)": "BD-CANADA-BUNDLE-2.0",
    "Best Doctors 360": "BD-360",
    "CCM BD Bundle - Complex Case Management": "CCM",
    "Chronic Condition Management Plus + MyStrength": "CCCMSC",
    "Comprehensive Prediabetes Care": "CMPRHNSVDIABETESPRVNTNCARE",
    "Comprehensive Weight Care (Select Populations)": "COMPREHENSIVEWEIGHTCARE",
    "Critical Case Support": "CC",
    "Curbside Consultation": "CUCO",
    "Dermatology": "DERM",
    "Diabetes Care": "DIABCARE",
    "Diabetes Flex": "DMDEVFLEX",
    "Diabetes Management Plus": "DMSOL",
    "Diabetes Management": "DIAB",
    "Elite Diagnostic Imaging Service": "EDIS",
    "Employee and Family Assistance Program": "EFAP",
    "Expert Medical Opinion 2.0 Bundle": "BD-USEMP-BUNDLE-2.0",
    "Expert Medical Opinion 2.0": "EMO2",
    "Expert Medical Opinion": "EMO",
    "Extended Family Benefit (Parents & In-Laws)": "EFB",
    "Find a Doctor": "FAD",
    "Find Best Care": "FBC",
    "Find Best Doctor": "FBD",
    "General Medical": "GM",
    "Global Care": "GLOBALCARE",
    "Health Library": "HEALTHLIBRARYHR",
    "Health Pro Referrals": "HPR",
    "Healthiest You Complete Bundle 2.0": "HY-CMUSEMP-BUNDLE-2.0",
    "Healthiest You Core Bundle": "HY-CRUSEMP-BUNDLE",
    "HealthiestYou": "HY",
    "Heart Failure": "HF",
    "Hypertension Care": "HYPTCARE",
    "Hypertension Management Plus": "CVSOL",
    "Hypertension Management": "HYPT",
    "Livongo BH 1.0": "LVBH-1.0",
    "Livongo BH 2.0": "LVBH-2.0",
    "Livongo Weight Management Powered by Retrofit": "WMRETRO",
    "Medical Director Access": "MDA",
    "Medical Record eSummary": "MRS",
    "Mental Health Care (Canada)": "MH",
    "Mental Health Care (US)": "BH",
    "Mental Health Coaching": "MYSTRPLUS",
    "Mental Health Complete": "MYSTR3",
    "Mental Health Digital": "MSDIGIT",
    "Mental Health Disability": "MHD",
    "Mental Health for Kids and Teens": "PEDMH",
    "Mental Health Navigator (INTL)": "MHN",
    "Mental Health Navigator (US)": "BHN",
    "MSK Hinge Bundle": "HINGE",
    "MYS - MyStrength Global": "MSGLOBAL",
    "MyStrength Solution": "MYSTRSOL",
    "Nutrition": "NUT",
    "Oncology Insight": "OI",
    "pathology": "pathology",
    "Prediabetes Care": "DIABPCARE",
    "Prediabetes Management Plus": "DPSOL",
    "Prediabetes Management": "DIABP",
    "Primary Care - PPPM": "PRIM360PPPM",
    "Primary360": "PRIM360CARE",
    "Provider Platform License": "PL",
    "Sexual Health": "sexual_health_pathology",
    "Sword DT": "SWORDDT",
    "TD Bundle - Included - greater than 1000": "TD-INCL-G1000",
    "TD Bundle - Included - less than 1000": "TD-INCL-L1000",
    "TD Bundle - Standard": "TD-STD",
    "Tobacco Cessation": "TC",
    "Transgender and Intersex Medical Advocacy Program": "TIMAP",
    "Treatment Decision Support": "TDS",
    "Virtual Care Optimization": "VCO",
    "Weight Management Care": "WEIGMCARE",
    "Weight Management": "WEIGM",
    "Wellness Health Risk Assessment": "WELLNESSHR"
}

### Apply the mapping to create the cc_product_code column
cc_product_code_col = None

for product, code in product_mapping.items():
    condition = col("Product__c") == product
    cc_product_code_col = when(condition, code) if cc_product_code_col is None else cc_product_code_col.when(condition, code)

### Create cc_product_code column
gab_psf_df_final = gab_psf_df_final.withColumn("cc_product_code", cc_product_code_col.otherwise(None))

# Map Visit Type names from Asset_Name__c column to their corresponding Visit Type Code required by Client Portal
visit_type_mapping = {
    "pathology": "",
    "Primary Care Annual Checkup Visit Fee": "PRIMCAREACF",
    "Primary360 Annual Checkup Visit Fee": "PRIMCAREACF",
    "Primary Care Initial Visit Fee": "NEWPATCF",
    "Primary360 Initial Visit Fee": "NEWPATCF",
    "Primary Care Ongoing Visit Fee": "PRIMCARECF",
    "Primary360 Ongoing Visit Fee": "PRIMCARECF",
    "Psychiatry Initial Visit Fee": "BHINIT",
    "Psychiatry Ongoing Visit Fee": "BHMD",
    "Psychologist Ongoing Visit Fee":"BHNONMDPSYCHOLOGY",
    "Therapy Ongoing Visit Fee": "BHNONMD"
}

### Apply the mapping to create the cc_product_visit_type column
cc_product_visit_type_col = None

for asset_name, visit_type in visit_type_mapping.items():
    condition = col("Asset_Name__c") == asset_name
    cc_product_visit_type_col = when(condition, visit_type) if cc_product_visit_type_col is None else cc_product_visit_type_col.when(condition, visit_type)

### Create cc_product_visit_type column
gab_psf_df_final = gab_psf_df_final.withColumn("cc_product_visit_type", cc_product_visit_type_col.otherwise(""))

# Create cc_total_consult_fees column and cast it to Double
gab_psf_df_final = gab_psf_df_final.withColumn("cc_total_consult_fees", col("Consult_Fee_Mbr_Pd__c") + col("Consult_Fee_Plan_Pd__c"))

gab_psf_df_final = gab_psf_df_final.withColumn("cc_total_consult_fees", col("cc_total_consult_fees").cast(DoubleType()))

# Create 'BD-CANADA-BUNDLE Membership Fee' column and cast it to Double
gab_psf_df_final = gab_psf_df_final.withColumn("BD-CANADA-BUNDLE Membership Fee",
                                                when((col("cc_product_code") == "BD-CANADA-BUNDLE") & (col("current_membership_fee").isNotNull()),
                                                col("current_membership_fee")).otherwise(None))

gab_psf_df_final = gab_psf_df_final.withColumn("BD-CANADA-BUNDLE Membership Fee", col("BD-CANADA-BUNDLE Membership Fee").cast(DoubleType()))

# Create 'BD-CANADA-BUNDLE-2.0 Membership Fee' column and cast it to Double
gab_psf_df_final = gab_psf_df_final.withColumn("BD-CANADA-BUNDLE-2 Membership Fee",
                                                when((col("cc_product_code") == "BD-CANADA-BUNDLE-2") & (col("current_membership_fee").isNotNull()),
                                                col("current_membership_fee")).otherwise(None))

gab_psf_df_final = gab_psf_df_final.withColumn("BD-CANADA-BUNDLE-2 Membership Fee", col("BD-CANADA-BUNDLE-2 Membership Fee").cast(DoubleType()))

# Fill Down BD-CANADA-BUNDLE Membership Fees
windowSpec = Window.orderBy("Member_Group__c", "cc_product_code").rowsBetween(Window.unboundedPreceding, Window.currentRow)

gab_psf_df_final = gab_psf_df_final.withColumn("BD-CANADA-BUNDLE Membership Fee", last("BD-CANADA-BUNDLE Membership Fee", ignorenulls=True).over(windowSpec))
gab_psf_df_final = gab_psf_df_final.withColumn("BD-CANADA-BUNDLE-2 Membership Fee", last("BD-CANADA-BUNDLE-2 Membership Fee", ignorenulls=True).over(windowSpec))

# Add 'cc_final_current_membership_fee' column with conditional logic and cast it to Double
gab_psf_df_final = gab_psf_df_final.withColumn(
    "cc_final_current_membership_fee",
    when((col("cc_product_code") == "EMO") & (col("BD-CANADA-BUNDLE Membership Fee").isNotNull()) & (col("BD-CANADA-BUNDLE Membership Fee") > col("current_membership_fee")), col("BD-CANADA-BUNDLE Membership Fee"))
    .when((col("cc_product_code") == "EMO2") & (col("BD-CANADA-BUNDLE-2 Membership Fee").isNotNull()) & (col("BD-CANADA-BUNDLE-2 Membership Fee") > col("current_membership_fee")), col("BD-CANADA-BUNDLE-2 Membership Fee"))
    .otherwise(col("current_membership_fee"))
)

gab_psf_df_final = gab_psf_df_final.withColumn("cc_final_current_membership_fee", col("cc_final_current_membership_fee").cast(DoubleType()))

# Filter rows where 'cc_product_code' is NOT "BD-CANADA-BUNDLE" or "BD-CANADA-BUNDLE-2.0"
gab_psf_df_final = gab_psf_df_final.filter(~col("cc_product_code").isin("BD-CANADA-BUNDLE", "BD-CANADA-BUNDLE-2.0"))

# Drop unnecessary columns
gab_psf_df_final = gab_psf_df_final.drop("current_membership_fee", "BD-CANADA-BUNDLE Membership Fee", "BD-CANADA-BUNDLE-2 Membership Fee")

# Perform a left join with 'Account' DF on 'Payer_Account__c'
gab_psf_df_final = gab_psf_df_final.join(gab_account_df.select("account_id", "account_name"), col("Payer_Account__c") == col("account_id"), "left_outer")

# Extract the first 15 characters of 'account_id'
gab_psf_df_final = gab_psf_df_final.withColumn("account_id", col("account_id").substr(1, 15))

# Perform a left join with 'Payers Admin Salesforce Match' DataFrame
gab_psf_df_final = gab_psf_df_final.join(raw_payers_excel_df, col("account_id") == col("Salesforce_Account_ID"), "left_outer")

# Drop unnecessary columns
gab_psf_df_final = gab_psf_df_final.drop("account_id", "Salesforce_Account_ID", "Salesforce_Account_Name")

# Rename columns
gab_psf_df_final = gab_psf_df_final.withColumnRenamed("account_name", "payer_account_name")

# Perform a left join with 'Account' DF on 'Sold_to_Account__c'
gab_psf_df_final = gab_psf_df_final.join(gab_account_df.select("account_id", "account_name"), col("Sold_to_Account__c") == col("account_id"), "left_outer")

# Drop unnecessary columns
gab_psf_df_final = gab_psf_df_final.drop("account_id")

# Rename columns
gab_psf_df_final = gab_psf_df_final.withColumnRenamed("account_name", "sold_to_account_name")

# Perform a left join with 'Account' DF on 'Bill_to_Account__c'
gab_psf_df_final = gab_psf_df_final.join(gab_account_df.select("account_id", "account_name"), col("Bill_to_Account__c") == col("account_id"), "left_outer")

# Drop unnecessary columns
gab_psf_df_final = gab_psf_df_final.drop("account_id")

# Rename columns
gab_psf_df_final = gab_psf_df_final.withColumnRenamed("account_name", "bill_to_account_name")

# Cast Product Start Date and Product End Date to Date
gab_psf_df_final = gab_psf_df_final.withColumn("Product_Start_Date__c", col("Product_Start_Date__c").cast(DateType()))
gab_psf_df_final = gab_psf_df_final.withColumn("Product_End_Date__c", col("Product_End_Date__c").cast(DateType()))

# Create list of Product Codes to exclude
excluded_codes = [
    "BD-CANADA-BUNDLE", "BD-CANADA-BUNDLE-2.0", "BD-USEMP-BUNDLE", "BD-USEMP-BUNDLE-2.0",
    "CCCMSC", "CCM", "CVSOL", "DIABCARE", "DIABPCARE", "DMSOL", "DPSOL", "EFB", "HINGE",
    "HY", "HY-CMUSEMP-BUNDLE-2.0", "HY-CRUSEMP-BUNDLE", "HYPTCARE", "LVBH-1.0", "MDA",
    "MH", "MYSTRSOL", "PL", "PRIM360PPPM", "SWORDDT", "TD-INCL-G1000", "TD-INCL-L1000",
    "TD-STD", "WEIGMCARE", "WMRETRO"
]

# Filter rows to exclude unnecessary Product Codes
gab_psf_df_final = gab_psf_df_final.filter(~(col("cc_product_code").isin(excluded_codes)))

# Filter rows to exclude Primary360 Initial Flex Visit Fee
gab_psf_df_final = gab_psf_df_final.filter(col("Asset_Name__c") != "Primary360 Initial Flex Visit Fee")

# Filter rows to exclude PSYCHOLOGY Visit Fee
gab_psf_df_final = gab_psf_df_final.filter(col("Asset_Name__c") != "Psychologist Ongoing Visit Fee")

# Set fee_type to PEPM for ALL Products of Canada Groups
gab_psf_df_final = gab_psf_df_final.withColumn("fee_type",
                                                when(col("business_region") == "Canada", "PEPM")
                                                .otherwise(col("fee_type")))

# Rename columns
gab_psf_df_final = gab_psf_df_final.withColumnsRenamed({
    "Id": "psf_id",
    "Name": "psf_number",
    "Member_Group__c": "member_group_id",
    "Member_Group_Name__c": "member_group_name",
    "Product_Start_Date__c": "product_start_date",
    "Product_End_Date__c": "product_end_date",
    "PSF_ProductCode__c": "psf_product_code",
    "Product__c": "product_name",
    "Actual_Copay_May_Be_Less__c": "actual_copay_may_be_less",
    "Consult_Fee_Mbr_Pd__c": "consult_fee_member",
    "Consult_Fee_Plan_Pd__c": "consult_fee_plan",
    "Asset_Name__c": "asset_name",
    "Asset__c": "asset_id",
    "Bill_to_Account__c": "bill_to_account_id",
    "Payer_Account__c": "payer_account_id",
    "Sold_to_Account__c": "sold_to_account_id",
    "Bill_To_Account_GUID__c": "bill_to_account_guid",
    "Payer_Account_GUID__c": "payer_account_guid",
    "Sold_To_Account_GUID__c": "sold_to_account_guid",
    "CreatedDate": "psf_created_date",
    "LastModifiedDate": "psf_last_modified_date",
    "USGH_APP_Opt_Out__c": "usgh_app_opt_out",
    "GLP_1_Model__c": "glp_1_model",
    "Payer_ID": "payer_id",
    "Payer_Name": "payer_name"
})

# Sort table
gab_psf_df_final = gab_psf_df_final.orderBy("psf_last_modified_date", "member_group_id", "cc_product_code", "asset_name", asc=[False, True, True, True])

# Save table to Lakehouse
if gab_psf_df_final.isEmpty() == False:
    gab_psf_df_final.write.format("delta") \
        .option("overwriteSchema", "true") \
        .mode("overwrite") \
        .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/5c03804a-6817-4f61-bdd3-d666573c958a/Tables/sf_lcrm_uat_gab_plan_specific_fees_200_silver")

    print("gab_psf_df_final table saved to Lakehouse successfully!")

display(gab_psf_df_final)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# # Print row count
# 
# row_count = gab_psf_df_final.count()
# 
# print(f"Total Rows: {row_count}")
# 
# # Print unique group_id
# 
# unique_count = gab_psf_df_final.select("member_group_id").distinct().count()
# 
# print(f"Unique values in member_group_id: {unique_count}")
