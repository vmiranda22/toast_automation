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

# # EDS Dev Gold Dataset: Admin Group Information Melted

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

# ##### Initialize Spark Session.

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

# ##### Load Silver tables and select columns.

# CELL ********************

admin_group_information_gold_df = spark.read.format("delta").load("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_group_information")

display(admin_group_information_gold_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Remove unnecessary columns.

# CELL ********************

columns_to_drop = [
    "effective_start_dt",
    "effective_end_dt",
    "source_group_root",
    "source_group_id",
    "notes_internal",
    "notes_external",
    "template",
    "created_at",
    "updated_at",
    "print_phone_organization_id",
    "print_url_organization_id",
    "direct_mail_organization_id",
    "email_organization_id",
    "incentive_organization_id",
    "outbound_calls_organization_id",
    "outbound_calls",
    "sms_text_organization_id",
    # "ancestry",
    # "parent_id",
    # "master_organization_id",
    # "master_organization_nm",
    "bill_to",
    "payer_id_combined",
    "payer_cd_combined",
    "payer_nm_combined",
    "payers_combined",
    "min_age_for_primary_registration",
    "min_age_for_dependent_registration",
    "max_age_for_dependent_registration",
    "sla_waive_visit_fee_if_missed",
    "hhs_access",
    "sso_only_access",
    "dual_access",
    "web_access",
    "mobile_access",
    "send_ccr_to_pcp",
    "disable_excuse_note",
    "send_card",
    "vip",
    "restricted_phi_access",
    "enable_two_factor_authentication",
    "authorized_consenter_allowed",
    "allow_manage_subscription",
    "allow_call_center_registration",
    "allow_call_center_consult_request",
    "in_home_rx_delivery",
    "send_promo_cd",
    "required_security_questions",
    "prohibit_member_attachment_download",
    "link_expiration_time",
    "date_of_birth_can_be_null",
    "performance_guarantee",
    "enable_wellness_content",
    "print_logo_filename",
    "membership_fee_type_cd",
    "refund_member",
    "send_member_resolution_letter",
    "send_problem_member_letter",
    "send_utilization_letter",
    "send_fraud_waste_abuse_letter",
    "annual_checkup_trigger_cd",
    "annual_checkup_start_month",
    "tpn_rule_id",
    "empi_namespace_cd",
    "benefit_restriction_cd",
    "standard_service_level",
    "vip_service_level"
]

admin_group_information_gold_df = admin_group_information_gold_df.drop(*columns_to_drop)

display(admin_group_information_gold_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Create the **MELTED** dataset with Group Settings data.

# CELL ********************

# Ensure we only bring in necessary columns from the start
excluded_columns = ["group_id", "legacy_group_id", "ancestry"]  # Removing only valid columns
setting_columns = [col for col in admin_group_information_gold_df.columns if col not in excluded_columns]

# Cast all setting columns to STRING
for col_name in setting_columns:
    admin_group_information_gold_df = admin_group_information_gold_df.withColumn(col_name, F.col(col_name).cast("STRING"))

# Construct the stack expression correctly
stack_expr = "stack({}, {})".format(
    len(setting_columns),
    ", ".join([f"'{col}', `{col}`" for col in setting_columns])  # Backticks for valid column references
)

# Perform the melt operation using `stack()`
melted_admin_group_information_gold_df = admin_group_information_gold_df.select(
    "group_id",
    "legacy_group_id",
    "ancestry",
    F.expr(stack_expr).alias("admin_setting_name", "admin_setting_value")
)

# Trim & remove duplicates
melted_admin_group_information_gold_df = (
    melted_admin_group_information_gold_df.withColumn("admin_setting_value", F.trim(F.col("admin_setting_value")))
    .dropDuplicates(["group_id", "legacy_group_id", "admin_setting_name", "admin_setting_value"]) 
    .orderBy("group_id", "admin_setting_name")
)

print(f"Total rows after melting: {melted_admin_group_information_gold_df.count()}")

display(melted_admin_group_information_gold_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Save the **MELTED** Dataset.

# CELL ********************

melted_admin_group_information_gold_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_300_gold_admin_group_information_melted")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }
