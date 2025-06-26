# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e29a63e5-b594-4b3c-a005-d9dd6019942a",
# META       "default_lakehouse_name": "toast_lh_ccvf_curated",
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

# toast_nb_validate_rule_syntax
# Utility to validate the syntax of condition expressions and expected values in rules

from pyspark.sql import SparkSession
from pyspark.sql.functions import expr, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, BooleanType, TimestampType
import logging

"""
Notebook: toast_nb_validate_rule_syntax

Purpose:
--------
This utility validates the syntax of rules defined in the workfront_validation_rules Delta table. 
It checks two main components for each rule:

1. `condition_expression`: Ensures that SQL-style filter expressions used to scope the rule 
   are syntactically valid and can be safely evaluated using Spark SQL `expr()`.

2. `expected_value`: Verifies that the expected values (used in equality comparisons) can be 
   interpreted correctly in Spark SQL expressions when applied to their respective field names.

Approach:
---------
- Loads the rule table from the Fabric Lakehouse Delta path.
- Constructs a dummy Spark DataFrame with expected column names to simulate expression evaluation.
- Iterates over each rule and uses `expr()` to test both the `condition_expression` and 
  `expected_value`.
- Catches and logs any syntax errors or unsupported formats.

Output:
-------
- Prints/logs any rules with invalid syntax for further inspection.
- Can be extended to:
  • Auto-deactivate invalid rules by setting `active = False`
  • Write results to an audit log table

Usage:
------
Intended for QA and validation of rules before they are used in the production evaluation engine.

Author: TOAST Team
"""

# === SETUP LOGGING ===
logger = logging.getLogger("ValidateRuleSyntax")
logging.basicConfig(level=logging.INFO)

# === START SPARK SESSION ===
spark = SparkSession.builder.getOrCreate()

# === CONFIGURATION ===
rules_table_path = "abfss://b08d383a-b8cc-4b8e-b189-d9d696a01977@onelake.dfs.fabric.microsoft.com/19d0a156-0ba5-48d9-ad24-2d55e56083dc/Tables/dbo/workfront_validation_rules"

# === LOAD RULES ===
logger.info("Loading rules from Delta table...")
df_rules = spark.read.format("delta").load(rules_table_path)

# === DEFINE DUMMY SCHEMA FOR TESTING ===
dummy_schema = StructType([
    StructField("gen_med_total_consult_fee", DoubleType(), True),
    StructField("psychiatry_ongoing_fee", DoubleType(), True),
    StructField("dermatology_total_consult_fee", DoubleType(), True),
    StructField("nutrition_membership_fee", DoubleType(), True),
    StructField("msk_total_consult_fee", DoubleType(), True),
    StructField("tobacco_cessation_total_consult_fee", DoubleType(), True),
    StructField("effective_start_date", TimestampType(), True),
    StructField("mental_health_total_consult_fee", DoubleType(), True),
    StructField("psychiatry_initial_visit_consult_fee", DoubleType(), True),
    StructField("membership_fee", DoubleType(), True),
    StructField("membership_fee_type", StringType(), True),
    StructField("consults_included", StringType(), True),
    StructField("mental_health_enabled", BooleanType(), True),
])

# === CREATE DUMMY DATAFRAME ===
dummy_df = spark.createDataFrame([tuple([None] * len(dummy_schema))], dummy_schema)

# === VALIDATION LOGIC ===
invalid_conditions = []
invalid_expected = []

for row in df_rules.collect():
    rule_id = row['rule_id']
    condition = row['condition_expression']
    field = row['field_name']
    expected = row['expected_value']

    # Validate condition_expression
    if condition not in [None, '', 'TRUE']:
        try:
            dummy_df.filter(expr(condition)).limit(1).collect()
        except Exception as e:
            logger.warning(f"Invalid condition in rule {rule_id}: {e}")
            invalid_conditions.append((rule_id, condition, str(e)))

    # Validate expected_value (only basic checks)
    if expected in ["NOT NULL", "< 240", "<= current_date", "BETWEEN 0 AND 2.5"]:
        continue  # skip template values for now

    try:
        dummy_df.withColumn("test", expr(f"{field} = {repr(expected)}" if expected not in ['true', 'false'] else f"{field} = {expected}"))
    except Exception as e:
        logger.warning(f"Invalid expected_value in rule {rule_id}: {e}")
        invalid_expected.append((rule_id, expected, str(e)))

# === OUTPUT RESULTS ===
if invalid_conditions:
    logger.warning("Some condition expressions are invalid:")
    for item in invalid_conditions:
        print(item)
else:
    logger.info("All condition expressions validated successfully.")

if invalid_expected:
    logger.warning("Some expected values are invalid:")
    for item in invalid_expected:
        print(item)
else:
    logger.info("All expected values validated successfully.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
