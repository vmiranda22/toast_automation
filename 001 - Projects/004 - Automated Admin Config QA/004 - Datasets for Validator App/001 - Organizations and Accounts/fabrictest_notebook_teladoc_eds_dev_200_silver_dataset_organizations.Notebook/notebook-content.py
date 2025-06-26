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

# # EDS Dev Silver Dataset: Melted & Unmelted - Organizations

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

base_path = "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/"

tables = {
    "organization_extensions": {
        "path": "teladoc_eds_dev_200_silver_organization_extensions",
        "columns": ["organization_id", "employer"] # "print_url", "print_phone", "additional_url"
    },
    
    #"organization_marketing_communications": {
    #    "path": "teladoc_eds_dev_200_silver_organization_marketing_communications",
    #    "columns": ["organization_id", "direct_mail", "email", "incentive", "outbound_calls", "sms_text"]
    #},

    "organization_user_relations": {
        "path": "teladoc_eds_dev_200_silver_organization_user_relations",
        "columns": ["organization_id", "user_id", "purpose_relation_type_cd"]
    },
    
    "organizations": {
        "path": "teladoc_eds_dev_200_silver_organizations",
        "columns": ["group_id", "cc_group_id", "organization_id", "organization_nm", "parent_id", "cc_master_organization_id", "ancestry",
                    "party_id", "print_url_org_id", "print_url", "print_phone_org_id", "print_phone",
                    "direct_mail_org_id", "direct_mail", "email_org_id", "email", "incentive_org_id", "incentive", "outbound_calls_org_id", "outbound_calls", "sms_text_org_id", "sms_text",
                    "created_at", "updated_at"]
    },

    "party_addresses": {
        "path": "teladoc_eds_dev_200_silver_party_addresses",
        "columns": ["party_id", "address_line_1", "address_line_2", "county", "city", "state_province", "postal", "country_cd", "address_type_cd"]
    },

    "persons": {
        "path": "teladoc_eds_dev_200_silver_persons",
        "columns": ["person_id", "party_id", "first_nm", "last_nm"]
    },

    "sales_reps": {
        "path": "teladoc_eds_dev_200_silver_sales_reps",
        "columns": ["sales_rep_id", "person_id", "sales_rep_type_cd"]
    }
}

dfs = {}

for name, details in tables.items():
    df = spark.read.format("delta").load(base_path + details["path"])

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

prefixes = {
    "organization_extensions": "oe_",
    #"organization_marketing_communications": "omc_",
    "organization_user_relations": "our_",
    "organizations": "o_",
    "party_addresses": "pa_",
    "persons": "p_",
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

# ##### Join Silver tables.

# CELL ********************

teladoc_eds_dev_dataset = dfs["organizations"].join(
    dfs["organization_extensions"],
    dfs["organizations"]["o_organization_id"] == dfs["organization_extensions"]["oe_organization_id"],
    how="left_outer"
)

# teladoc_eds_dev_dataset = teladoc_eds_dev_dataset.join(
#    dfs["organization_marketing_communications"],
#    teladoc_eds_dev_dataset["o_organization_id"] == dfs["organization_marketing_communications"]["omc_organization_id"],
#    how="left_outer"
# )

teladoc_eds_dev_dataset = teladoc_eds_dev_dataset.join(
    dfs["party_addresses"],
    teladoc_eds_dev_dataset["o_party_id"] == dfs["party_addresses"]["pa_party_id"],
    how="left_outer"
)

teladoc_eds_dev_dataset = teladoc_eds_dev_dataset.join(
    dfs["organization_user_relations"],
    teladoc_eds_dev_dataset["o_organization_id"] == dfs["organization_user_relations"]["our_organization_id"],
    how="left_outer"
)

teladoc_eds_dev_dataset = teladoc_eds_dev_dataset.join(
    dfs["sales_reps"],
    teladoc_eds_dev_dataset["our_user_id"] == dfs["sales_reps"]["sr_sales_rep_id"],
    how="left_outer"
)

teladoc_eds_dev_dataset = teladoc_eds_dev_dataset.join(
    dfs["persons"],
    teladoc_eds_dev_dataset["sr_person_id"] == dfs["persons"]["p_person_id"],
    how="left_outer"
)

teladoc_eds_dev_dataset.orderBy(["o_organization_id"])

display(teladoc_eds_dev_dataset)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Remove unnecessary columns.

# CELL ********************

columns_to_drop = [
    "o_party_id",
    "o_ancestry",
    "o_created_at",
    "o_updated_at",
    "oe_organization_id",
    "omc_organization_id",
    "pa_party_id",
    "our_organization_id",
    "our_user_id",
    "sr_sales_rep_id",
    "sr_person_id",
    "p_person_id",
    "p_party_id"
]

teladoc_eds_dev_dataset = teladoc_eds_dev_dataset.drop(*columns_to_drop)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Save the Silver Dataset **UNMELTED**.

# CELL ********************

teladoc_eds_dev_dataset.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_dataset_organizations")

print("✅ Dataset saved!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Create the **MELTED** dataset with Group Settings data.

# CELL ********************

# Ensure we only bring in necessary columns from the start
excluded_columns = ["o_organization_id"]  # Removing only valid columns
setting_columns = [col for col in teladoc_eds_dev_dataset.columns if col not in excluded_columns]

# Cast all setting columns to STRING
for col_name in setting_columns:
    teladoc_eds_dev_dataset = teladoc_eds_dev_dataset.withColumn(col_name, F.col(col_name).cast("STRING"))

# Construct the stack expression correctly
stack_expr = "stack({}, {})".format(
    len(setting_columns),
    ", ".join([f"'{col}', `{col}`" for col in setting_columns])  # Backticks for valid column references
)

# Perform the melt operation using `stack()`
teladoc_eds_dev_dataset_melted = teladoc_eds_dev_dataset.select(
    "o_organization_id",
    F.expr(stack_expr).alias("admin_setting_name", "admin_setting_value")
)

# Trim & remove duplicates
teladoc_eds_dev_dataset_melted = (
    teladoc_eds_dev_dataset_melted.withColumn("admin_setting_value", F.trim(F.col("admin_setting_value")))
    .dropDuplicates(["o_organization_id", "admin_setting_name", "admin_setting_value"])  # Removed o_organization_nm if not present
    .orderBy("o_organization_id")
)

print(f"Total rows after melting: {teladoc_eds_dev_dataset_melted.count()}")
print(teladoc_eds_dev_dataset_melted.columns)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Display **MELTED** dataset.

# CELL ********************

display(teladoc_eds_dev_dataset_melted)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Save the Silver Dataset **MELTED**.

# CELL ********************

teladoc_eds_dev_dataset_melted.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/4b9a8e2d-64db-464e-b218-053f22ac13b1/Tables/teladoc_eds_dev_200_silver_melted_dataset_organizations_settings")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }
