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

# # Salesforce (LCRM) UAT dataset.

# MARKDOWN ********************

# Import.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

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

# Load required tables.

# CELL ********************

df_salesforce_lcrm_uat_account = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_100_bronze_account")
df_salesforce_lcrm_uat_member_group = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_100_bronze_member_group")
df_salesforce_lcrm_uat_plan_specific_fees_by_product = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_100_bronze_plan_specific_fees")
df_salesforce_lcrm_uat_subscription = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/salesforce_uat_100_bronze_subscription")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# MARKDOWN ********************

# Select columns.


# CELL ********************

df_salesforce_lcrm_uat_account = (
    df_salesforce_lcrm_uat_account.select(
        "Id",
        "Name",
        "SystemModstamp"
    )
)

df_salesforce_lcrm_uat_member_group = (
    df_salesforce_lcrm_uat_member_group.select(
        "Id",
        "Name",
        "Name__c",
        "Client_Account__c",        
        "Group_Number__c",
        "Status__c",
        "Migration_Group_Number__c",
        "Client_Account_Manager__c",
        "Active_Date__c",
        "Termination_Date__c",
        "Domestic_Country__c",
        "Co_Brand_with_Logo__c",
        "AltLogo1_ID__c",
        "AltLogo1__c",
        "AltLogo2_ID__c",
        "AltLogo2__c",
        "Any_Special_Instructions__c",
        "Card_Template__c",
        "Actual_Copay_May_Be_Less__c",
        "Allow_Caregiver_Program__c",
        "Allow_Conversion_to_Retail__c",
        "Card_Name__c",
        "Allow_Geo_Fencing__c",
        "Health_Assistant__c",
        "Enable_Livongo_Combined_Eligibility__c",
        "Enable_Livongo_Referrals__c",
        "Livongo_Registration_code__c",
        "Enable_Chronic_Care_Referrals__c",
        "SystemModstamp"
    )
)

df_salesforce_lcrm_uat_plan_specific_fees_by_product = (
    df_salesforce_lcrm_uat_plan_specific_fees_by_product.select(
        "Id",
        "Member_Group__c",
        "Name",
        "Subscription__c",
        "Consult_Fee_Mbr_Pd__c",
        "Consult_Fee_Plan_Pd__c"
    )
)

df_salesforce_lcrm_uat_subscription = (
    df_salesforce_lcrm_uat_subscription.select(
        "Id",
        "SBQQ__Product__c",
        "SBQQ__ProductId__c",
        "Name",
        "Current_Membership_Fee__c"
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Function to add prefix.

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

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Apply prefix.

# CELL ********************

df_salesforce_lcrm_uat_account = add_prefix(df_salesforce_lcrm_uat_account, "ACCT_")
df_salesforce_lcrm_uat_member_group = add_prefix(df_salesforce_lcrm_uat_member_group, "MG_")
df_salesforce_lcrm_uat_plan_specific_fees_by_product = add_prefix(df_salesforce_lcrm_uat_plan_specific_fees_by_product, "PSF_")
df_salesforce_lcrm_uat_subscription = add_prefix(df_salesforce_lcrm_uat_subscription, "SUB_")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# MARKDOWN ********************

# Join.

# CELL ********************

lcrm_df = df_salesforce_lcrm_uat_account.join(
    df_salesforce_lcrm_uat_member_group,
    df_salesforce_lcrm_uat_account["ACCT_Id"] == df_salesforce_lcrm_uat_member_group["MG_Client_Account__c"],
    how="left_outer"
)

lcrm_df = lcrm_df.join(
    df_salesforce_lcrm_uat_plan_specific_fees_by_product,
    lcrm_df["MG_Id"] == df_salesforce_lcrm_uat_plan_specific_fees_by_product["PSF_Member_Group__c"],
    how="left_outer"
)

lcrm_df = lcrm_df.join(
    df_salesforce_lcrm_uat_subscription,
    lcrm_df["PSF_Subscription__c"] == df_salesforce_lcrm_uat_subscription["SUB_Id"],
    how="left_outer"
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Filter df.

# CELL ********************

lcrm_df = lcrm_df.filter(lcrm_df["MG_Client_Account__c"] == "001f400000dG3sjAAC")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# MARKDOWN ********************

# Save back to lakehouse with new schema.

# CELL ********************

lcrm_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/lcrm_dataset")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }
