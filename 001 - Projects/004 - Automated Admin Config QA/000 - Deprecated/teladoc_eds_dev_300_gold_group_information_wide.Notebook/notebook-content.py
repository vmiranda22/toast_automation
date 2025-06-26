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

# This notebook creates the dataset with Member Group information (excluding Product information).
# Comments:
# Source should be silver tables, not bronze.

# MARKDOWN ********************

# Import.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import pandas as pd
from functools import reduce

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Initialize session.

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

# Load and filter tables and select columns.

# CELL ********************

base_path = "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/"

tables = {
    "organizations": {
        "path": "teladoc_eds_dev_100_bronze_organizations_",
        "columns": [
            "organization_id", "organization_nm", "parent_id", "ancestry", "ancestry_depth",
            "sql_path", "lft", "rgt", "group_id", "party_id", "created_at", "created_by",
            "updated_at", "updated_by"
        ]
    },
    "groups": {
        "path": "teladoc_eds_dev_100_bronze_groups_",
        "filter": (F.col("template") == 0) & (F.col("exclusion_cd") == "IN"),
        "columns": [
            "group_id", "group_nm", "effective_start_dt", "effective_end_dt",
            "registration_group_cd", "card_nm", "source_group_root",
            "source_group_identifer", "group_type_cd", "data_source_cd",
            "created_at", "created_by", "updated_at", "updated_by", "legacy_group_id"
        ]
    },
    "group_settings": {
        "path": "teladoc_eds_dev_100_bronze_group_settings_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": [
            "group_id", "domestic_country_cd", "lob_cd", "one_app_flg",
            "sso_only_access_flg", "dual_access_allowed_flg", "web_access_flg",
            "mobile_access_flg", "send_ccr_to_pcp_flg", "disable_excuse_note_flg",
            "send_card_flg", "welcome_kit_retro_flg", "allow_conversion_to_retail_flg",
            "vip_flg", "ccr_cannot_access_member_phi_flg", "enable_geo_fencing",
            "enable_two_factor_auth", "authorized_consenter_allowed_flg",
            "allow_manage_subscription_flg", "allow_call_center_registration_flg",
            "allow_call_center_consult_request_flg", "allow_health_assistant_flg",
            "in_home_rx_delivery_flg", "send_promo_cd_flg",
            "required_security_question_cnt", "chronic_care_referral_flg",
            "chronic_care_joint_eligibility_flg",
            "prohibit_member_attachment_download_flg",
            "quick_registration_link_expiration_min", "dob_can_be_null", "pg_flg",
            "enable_wellness_content_flg", "minor_registration_flg",
            "min_age_for_dependent_registration", "max_age_for_dependent_registration",
            "min_age_for_primary_registration", "allow_sla_reimbursement_flg",
            "default_billing_fee_type_cd", "single_invoice_ccm_flg", "created_at",
            "created_by", "updated_at", "updated_by"
        ]
    },
    "ref_countries": {
        "path": "teladoc_eds_dev_100_bronze_ref_countries_",
        "columns": ["country_cd", "country_nm", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "alt_group_ids": {
        "path": "teladoc_eds_dev_100_bronze_alt_group_ids_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["alt_group_cd", "alt_group_value", "group_id", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "valid_group_sources": {
        "path": "teladoc_eds_dev_100_bronze_valid_group_sources_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["group_id", "primary_source_cd", "dependent_source_cd", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "group_service_level_relations": {
        "path": "teladoc_eds_dev_100_bronze_group_service_level_relations_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["group_id", "standard_service_level_id", "vip_service_level_id", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "ref_service_levels_standard": {
        "path": "teladoc_eds_dev_100_bronze_ref_service_levels_",
        "columns": ["ref_service_level_id", "service_level_nm", "level1", "level2", "level3", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "ref_service_levels_vip": {
        "path": "teladoc_eds_dev_100_bronze_ref_service_levels_",
        "columns": ["ref_service_level_id", "service_level_nm", "level1", "level2", "level3", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "group_payer_relations": {
        "path": "teladoc_eds_dev_100_bronze_group_payer_relations_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["group_id", "payer_id", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "payers": {
        "path": "teladoc_eds_dev_100_bronze_payers_",
        "columns": ["payer_id", "payer_nm", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "group_billing_relations": {
        "path": "teladoc_eds_dev_100_bronze_group_billing_relations_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["group_id", "billing_id", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "billings": {
        "path": "teladoc_eds_dev_100_bronze_billings_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["organization_id", "billing_id", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "organization_user_relations": {
        "path": "teladoc_eds_dev_100_bronze_organization_user_relations_",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["organization_id", "purpose_relation_type_cd", "user_id", "created_at", "created_by", "updated_at", "updated_by"]
    },
    "sales_reps": {
        "path": "teladoc_eds_dev_100_bronze_sales_rep",
        "filter": F.col("exclusion_cd") == "IN",
        "columns": ["sales_rep_id", "sales_rep_type_cd", "created_at", "created_by", "updated_at", "updated_by"]
    }
}

dfs = {}

for name, details in tables.items():
    df = spark.read.format("delta").load(base_path + details["path"])

    if "filter" in details:
        df = df.filter(details["filter"])

    if "columns" in details:
        df = df.select(*details["columns"])
    
    dfs[name] = df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# MARKDOWN ********************

# Function to add prefix.

# CELL ********************

def add_prefix(df, prefix):
  fabrictest_lakehouse
Tables
 0 sections have been expanded and 0 cells are now hidden Cell execution canceled


[57]
1234
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import pandas as pd
from functools import reduce
1 sec
 - Command executed in 231 ms by Ray Montero on 1:32:18 PM, 2/24/25
Output is hidden

[58]
123
spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInRead", "LEGACY")
spark.conf.set("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")
1 sec
 - Command executed in 233 ms by Ray Montero on 1:32:18 PM, 2/24/25

[59]
123456789101112131415161718192021222324252627282930313233343536373839404142434445464748495051525354555657585960616263646566676869707172737475767778798081828384858687888990919293949596979899100101102103104105106107108109110111112113114115

    if "columns" in details:
        df = df.select(*details["columns"])
    
    dfs[name] = df
3 sec
 - Command executed in 3 sec 541 ms by Ray Montero on 1:32:22 PM, 2/24/25

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

# Apply prefix.

# CELL ********************

prefixes = {
    "organizations": "o_",
    "groups": "g_",
    "group_settings": "gs_",
    "ref_countries": "rc_",
    "alt_group_ids": "agi_",
    "valid_group_sources": "vgs_",
    "group_service_level_relations": "gslr_",
    "ref_service_levels_standard": "rsls_",
    "ref_service_levels_vip": "rslv_",
    "group_payer_relations": "gpr_",
    "payers": "p_",
    "group_billing_relations": "gbr_",
    "billings": "b_",
    "organization_user_relations": "our_",
    "sales_reps": "sr_"
}

for name, prefix in prefixes.items():
    if name in dfs:
        dfs[name] = add_prefix(dfs[name], prefix)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Approach to get inherited fields, starting with organization_user_relations.

# CELL ********************

# Convert Spark DataFrames to Pandas for recursive processing.
organizations_pd = dfs["organizations"].select("o_organization_id", "o_parent_id", "o_group_id").toPandas()
organizations_user_relations_pd = dfs["organization_user_relations"].select("our_organization_id", "our_user_id").toPandas()

# Create dictionaries for hierarchy mapping.
organization_hierarchy = organizations_pd.set_index("o_organization_id")["o_parent_id"].to_dict()
organization_user_id = organizations_user_relations_pd.set_index("our_organization_id")["our_user_id"].to_dict()

# Function to find the first parent organization with a user_id.
def find_first_parent_with_user(org_id):
    while org_id in organization_hierarchy:
        if org_id in organization_user_id and pd.notna(organization_user_id[org_id]):
            return str(org_id)  # Convert to string for Spark compatibility.
        org_id = organization_hierarchy[org_id]  # Move up the hierarchy.
    return None  # No parent found.

# Apply function to all organizations.
organizations_pd["first_parent_id_with_user_id"] = organizations_pd["o_organization_id"].apply(find_first_parent_with_user)

# Ensure correct data types before converting back to Spark.
organizations_pd = organizations_pd.astype({"o_organization_id": str, "first_parent_id_with_user_id": str})

# Convert back to Spark DataFrame.
organizations_df = spark.createDataFrame(organizations_pd)

# Store back into the dfs dictionary.
dfs["organizations"] = organizations_df

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

org_child = dfs["organizations"].alias("child").selectExpr(
    "o_organization_id as child_o_organization_id",
    "o_parent_id as child_o_parent_id",
    "o_group_id as child_o_group_id",
    "*" # Need to remove this so I don't end up with duplicate columns.
)

org_parent = dfs["organizations"].alias("parent").selectExpr(
    "o_organization_id as parent_o_organization_id",
    "o_parent_id as parent_o_parent_id",
    "o_group_id as parent_o_group_id",
    "*" # Need to remove this so I don't end up with duplicate columns.
)

join_list = [
    (dfs["groups"], org_child["child_o_group_id"] == dfs["groups"]["g_group_id"], "inner"),
    (dfs["group_settings"], dfs["groups"]["g_group_id"] == dfs["group_settings"]["gs_group_id"], "inner"),
    (dfs["ref_countries"], dfs["group_settings"]["gs_domestic_country_cd"] == dfs["ref_countries"]["rc_country_cd"], "inner"),
    (dfs["alt_group_ids"], dfs["groups"]["g_group_id"] == dfs["alt_group_ids"]["agi_group_id"], "inner"),
    (dfs["valid_group_sources"], dfs["groups"]["g_group_id"] == dfs["valid_group_sources"]["vgs_group_id"], "inner"),
    (dfs["group_service_level_relations"], dfs["groups"]["g_group_id"] == dfs["group_service_level_relations"]["gslr_group_id"], "inner"),
    (dfs["ref_service_levels_standard"], dfs["group_service_level_relations"]["gslr_standard_service_level_id"] == dfs["ref_service_levels_standard"]["rsls_ref_service_level_id"], "inner"),
    (dfs["ref_service_levels_vip"], dfs["group_service_level_relations"]["gslr_vip_service_level_id"] == dfs["ref_service_levels_vip"]["rslv_ref_service_level_id"], "inner"),
    (dfs["group_billing_relations"], dfs["groups"]["g_group_id"] == dfs["group_billing_relations"]["gbr_group_id"], "left"),
    (dfs["billings"], dfs["group_billing_relations"]["gbr_billing_id"] == dfs["billings"]["b_billing_id"], "left"),
    (dfs["group_payer_relations"], dfs["groups"]["g_group_id"] == dfs["group_payer_relations"]["gpr_group_id"], "left"),
    (dfs["payers"], dfs["group_payer_relations"]["gpr_payer_id"] == dfs["payers"]["p_payer_id"], "left"),
    (dfs["organization_user_relations"], org_child["child_o_parent_id"] == dfs["organization_user_relations"]["our_organization_id"], "left"),
    (dfs["sales_reps"], dfs["organization_user_relations"]["our_user_id"] == dfs["sales_reps"]["sr_sales_rep_id"], "left"),
    (org_parent, org_child["child_o_parent_id"] == org_parent["parent_o_organization_id"], "inner"),  # Fully qualified reference
]

teladoc_eds_df = reduce(lambda df, join_info: df.join(join_info[0], join_info[1], join_info[2]), join_list, org_child)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Drop unnecesary columns.

# CELL ********************

columns_to_drop = [ "o_organization_id",
                    "o_parent_id",
                    "o_group_id",
                    "o_party_id",
                    "o_created_at",
                    "o_created_by",
                    "o_updated_at",
                    "o_updated_by",
                    "g_created_at",
                    "g_created_by",
                    "g_updated_at",
                    "g_updated_by",
                    "gs_created_at",
                    "gs_created_by",
                    "gs_updated_at",
                    "gs_updated_by",
                    "rc_created_at",
                    "rc_created_by",
                    "rc_updated_at",
                    "rc_updated_by",
                    "agi_group_id",
                    "agi_created_at",
                    "agi_created_by",
                    "agi_updated_at",
                    "agi_updated_by",
                    "vgs_group_id",
                    "vgs_primary_source_cd",
                    "vgs_dependent_source_cd",
                    "vgs_created_at",
                    "vgs_created_by",
                    "vgs_updated_at",
                    "vgs_updated_by",
                    "gslr_group_id",
                    "gslr_standard_service_level_id",
                    "gslr_vip_service_level_id",
                    "gslr_created_at",
                    "gslr_created_by",
                    "gslr_updated_at",
                    "gslr_updated_by",
                    "rsls_ref_service_level_id",
                    "rsls_created_at",
                    "rsls_created_by",
                    "rsls_updated_at",
                    "rsls_updated_by",
                    "rslv_ref_service_level_id",
                    "rslv_created_at",
                    "rslv_created_by",
                    "rslv_updated_at",
                    "rslv_updated_by",
                    "gpr_group_id",
                    "gpr_payer_id",
                    "gpr_created_at",
                    "gpr_created_by",
                    "gpr_updated_at",
                    "gpr_updated_by",
                    "p_payer_id",
                    "p_payer_nm",
                    "p_created_at",
                    "p_created_by",
                    "p_updated_at",
                    "p_updated_by",
                    "gbr_group_id",
                    "gbr_billing_id",
                    "gbr_created_at",
                    "gbr_created_by",
                    "gbr_updated_at",
                    "gbr_updated_by",
                    "b_billing_id",
                    "b_created_at",
                    "b_created_by",
                    "b_updated_at",
                    "b_updated_by",
                    "our_organization_id",
                    "our_purpose_relation_type_cd",
                    "our_user_id",
                    "our_created_at",
                    "our_created_by",
                    "our_updated_at",
                    "our_updated_by",
                    "sr_sales_rep_id",        
                    "sr_created_at",
                    "sr_created_by",
                    "sr_updated_at",
                    "sr_updated_by"]

teladoc_eds_df = teladoc_eds_df.drop(*columns_to_drop)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Unpivot.

# CELL ********************

# Ensure we only bring in necessary columns from the start
excluded_columns = {"child_o_group_id"}  # Removing only valid columns
selected_columns = [col for col in teladoc_eds_df.columns if col not in excluded_columns]

# Drop ambiguity by explicitly selecting necessary columns and aliasing parent columns
teladoc_eds_df = teladoc_eds_df.select(
    F.col("child_o_organization_id").alias("o_organization_id"),
    F.col("child_o_group_id").alias("o_group_id"),
    F.col("parent_o_organization_id").alias("parent_organization_id"),
    *[F.col(col) for col in selected_columns if col.startswith("gs_") or col.startswith("rc_") or col.startswith("agi_") or col.startswith("rsl")]
)

# Identify setting columns (everything except explicitly required ones)
required_columns = {"o_organization_id", "o_group_id", "parent_organization_id"}
setting_columns = [col for col in teladoc_eds_df.columns if col not in required_columns]

# Cast all setting columns to STRING
for col_name in setting_columns:
    teladoc_eds_df = teladoc_eds_df.withColumn(col_name, F.col(col_name).cast("STRING"))

# Construct the stack expression correctly
stack_expr = "stack({}, {})".format(
    len(setting_columns),
    ", ".join([f"'{col}', `{col}`" for col in setting_columns])  # Backticks for valid column references
)

# Perform the melt operation using `stack()`
melted_df = teladoc_eds_df.select(
    "o_organization_id",
    "o_group_id",
    "parent_organization_id",
    F.expr(stack_expr).alias("name", "value")
)

# Trim & remove duplicates
melted_df = (
    melted_df.withColumn("value", F.trim(F.col("value")))
    .dropDuplicates(["o_organization_id", "name", "value"])  # Removed o_organization_nm if not present
    .orderBy("o_organization_id")
)

print(f"Total rows after melting: {melted_df.count()}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Save to lakehouse with new schema.

# CELL ********************

melted_df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_member_group_settings")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }
