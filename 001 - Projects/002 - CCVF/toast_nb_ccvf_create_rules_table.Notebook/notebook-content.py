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

# toast_nb_create_rules_table
# Notebook to create the validation_rules Delta table for long-format config evaluation

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, BooleanType, IntegerType, TimestampType
)
from datetime import datetime, timezone
import logging

# === SETUP LOGGING ===
logger = logging.getLogger("CreateRulesTable")
logging.basicConfig(level=logging.INFO)

# === START SPARK SESSION ===
spark = SparkSession.builder.getOrCreate()

# === CONFIGURATION ===
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
lakehouse_id = "e29a63e5-b594-4b3c-a005-d9dd6019942a"
rules_table_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/dbo/validation_rules"

# === DEFINE SCHEMA FOR LONG FORMAT ===
logger.info("Defining validation rules schema for long-format config table...")
validation_rules_schema = StructType([
    StructField("rule_id", StringType(), False),
    StructField("rule_name", StringType(), True),
    StructField("rule_scope", StringType(), True),
    StructField("system", StringType(), True),
    StructField("admin_organization_id", StringType(), True),
    StructField("salesforce_lcrm_account_id", StringType(), True),
    StructField("field_name", StringType(), False),
    StructField("expected_value", StringType(), False),
    StructField("comparison_operator", StringType(), True),
    StructField("condition_expression", StringType(), True),
    StructField("priority", IntegerType(), True),
    StructField("active", BooleanType(), False),
    StructField("created_at", TimestampType(), False),
    StructField("created_by", StringType(), False),
    StructField("is_dependent", BooleanType(), False)
])

# === SAMPLE DATA ===
logger.info("Creating sample data for long-format rule evaluation...")
now = datetime.utcnow()

sample_data = [
    (
        "1",                                        # rule_id
        "Consult Billing Method must not be null", # rule_name
        "global",                                   # scope (global or account)
        "salesforce_lcrm",                          # system
        None,                                       # admin_organization_id
        "001f400000dGS7yAAG",                       # salesforce_lcrm_account_id
        "consult_billing_method",                   # field_name
        "NOT NULL",                                 # expected_value
        "=",                                        # comparison_operator
        None,                                       # condition_expression
        1,                                          # priority
        True,                                       # active
        now,                                        # created_at
        "system_admin",                             # created_by
        False                                       # is_dependent
    ),
    (
        "2",                             # rule_id
        "Geo-fencing must be enabled",   # rule_name
        "account",                       # scope (global or account)
        "salesforce_lcrm",               # system
        None,                            # admin_organization_id
        "001XXXXXXXXXXXXXXX",            # salesforce_lcrm_account_id
        "allow_geo_fencing",             # field_name
        "true",                          # expected_value
        "=",                             # comparison_operator
        None,                            # condition_expression
        2,                               # priority
        True,                            # active
        now,                             # created_at
        "system_admin",                  # created_by
        False                            # is_dependent
    ),
]

# === CREATE DATAFRAME ===
logger.info("Creating DataFrame from sample data...")
df_rules = spark.createDataFrame(sample_data, schema=validation_rules_schema)

# === SAVE TO DELTA ===
logger.info(f"Saving validation rules table to: {rules_table_path}")
df_rules.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .option("mergeSchema", "true") \
    .save(rules_table_path)
logger.info("Validation rules table saved successfully.")

# === REGISTER TABLE IN CATALOG ===
logger.info("Registering table in Lakehouse catalog as 'dbo.validation_rules'")
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS dbo.validation_rules
    USING DELTA
    LOCATION '{rules_table_path}'
""")
logger.info("Table registered successfully in catalog.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
