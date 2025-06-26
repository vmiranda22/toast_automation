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

# toast_nb_eval_config_rules

"""
Validation Engine for Long-Format Configuration Data with Rule Type Optimization and Diagnostic Logging

This notebook validates client configuration stored in long format against business rules. 
It supports both simple rules (single-field checks) and dependent rules (cross-field logic) and uses
structured logging to assist in debugging and transparency.

Key Features:
-------------
- Categorizes rules by `rule_type` ("simple" or "dependent")
- Supports optional `condition_expression` for filtering before evaluation
- Applies optimized filtering and joins based on rule type
- Calculates PASS/FAIL using expected value and comparison operator
- Logs detailed information for each rule, including:
    • Field and client ID targeted
    • Filtered row counts at each stage (field match, condition match, result count)
    • Full pass/fail evaluation expression
    • Join diagnostics for dependent rules
    • Skipped rules due to missing matches or errors

Data Model:
-----------
1. Configuration Data (`df_config`):
   - Columns:
     - `MG_id`, `ancestry`, `salesforce_setting_name`, `salesforce_setting_value`

2. Rules Table (`df_rules`):
   - Columns:
     - `rule_id`, `rule_name`, `client_id`, `field_name`, `expected_value`,
       `comparison_operator`, `condition_expression`, `rule_type`, `priority`, `active`, `created_at`

Processing Flow:
----------------
1. Load configuration data and business rules from Delta Lake.
2. Split rules by type:
   - Simple: Evaluate directly on target field with optional condition.
   - Dependent: Join with other fields on `MG_id`, apply cross-field condition.
3. Evaluate PASS/FAIL for all matching rows using:
   - Equality, NOT NULL, BETWEEN, IN, NOT IN, and other expressions.
4. Aggregate results across all rules into a unified DataFrame.
5. Write results to Delta table for downstream reporting or analysis.

Output:
-------
- Delta table at `config_validation_results` containing:
    • `client_id`, `MG_id`, `field_name`, `actual_value`, `expected_value`,
      `comparison_operator`, `pass_fail`, `rule_id`, `rule_name`

Use this notebook to verify the completeness and correctness of configuration values
submitted by client implementations. Logs are designed to assist in tracing skipped or
empty results, making it easier to understand why a rule evaluation failed or returned no data.

Author: Ramiro Montero
"""


from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, expr, concat
from typing import List
import logging

# === SETUP LOGGING ===
logger = logging.getLogger("EvaluationEngine")
logging.basicConfig(level=logging.INFO)

# === START SPARK SESSION ===
spark = SparkSession.builder.getOrCreate()

# === CONFIGURATION ===
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
lakehouse_id = "e29a63e5-b594-4b3c-a005-d9dd6019942a"

CONFIG_DATA_PATH = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/dbo/salesforce_lcrm_member_group_settings_melted_trusted"
RULES_PATH = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/dbo/validation_rules"
OUTPUT_PATH = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/dbo/config_validation_results"

# === LOAD DATA ===
logger.info("Loading config data and rules...")
df_config = spark.read.format("delta").load(CONFIG_DATA_PATH)
df_rules = spark.read.format("delta").load(RULES_PATH).filter("active = true")
rules = df_rules.collect()
logger.info(f"Loaded {len(rules)} active rules. Starting evaluation...")

def evaluate_rules_long(df_config: DataFrame, rules: List) -> DataFrame:
    results = []

    for rule in rules:
        rule_id = rule["rule_id"]
        system = rule["system"].lower()
        scope = rule["scope"].lower()
        org_id = rule["admin_organization_id"]
        account_id = rule["salesforce_lcrm_account_id"]
        field_name = rule["field_name"]
        expected_value = rule["expected_value"]
        comparison_operator = rule["comparison_operator"] or "="
        condition = rule["condition_expression"]
        rule_name = rule["rule_name"]
        rule_type = "dependent" if rule["is_dependent"] else "simple"
        client_id = account_id or org_id  # for logging

        logger.info(f"---\nEvaluating Rule {rule_id} [{rule_type}]: {rule_name}")
        logger.info(f"Target field: {field_name}, Expected value: {expected_value}, Operator: {comparison_operator}")
        logger.info(f"Scope: {scope}, System: {system}")
        logger.info(f"Condition expression: {condition if condition else '[None]'}")

        # === Apply scope + system-based filtering ===
        if scope == "global":
            df_config_scoped = df_config
            logger.info(f"Rule {rule_id} has GLOBAL scope. Evaluating full dataset.")
        elif scope == "acct":
            if system == "salesforce_lcrm":
                df_config_scoped = df_config.filter(col("account_id") == account_id)
                logger.info(f"Rule {rule_id} is ORG scoped. Filtering where account_id = {account_id}")
            elif system == "admin":
                df_config_scoped = df_config.filter(col("org_id") == org_id)
                logger.info(f"Rule {rule_id} is ORG scoped. Filtering where org_id = {org_id}")
            elif system == "both":
                df_config_scoped = df_config.filter(
                    (col("account_id") == account_id) & (col("org_id") == org_id)
                )
                logger.info(f"Rule {rule_id} is ORG scoped and applies to BOTH systems. Filtering on account_id = {account_id} and org_id = {org_id}")
            else:
                logger.warning(f"Unknown system '{system}' in rule {rule_id}. Skipping.")
                continue
        else:
            logger.warning(f"Unknown scope '{scope}' in rule {rule_id}. Skipping.")
            continue

        scoped_count = df_config_scoped.count()
        logger.info(f"Rows after scope/system filtering: {scoped_count}")
        if scoped_count == 0:
            logger.warning(f"No rows after scope/system filter for rule {rule_id}. Skipping.")
            continue

        # === Filter config to target records ===
        df_target = df_config_scoped.filter(col("salesforce_setting_name") == field_name)

        target_count = df_target.count()
        logger.info(f"Target records matching field '{field_name}': {target_count}")

        if target_count == 0:
            logger.warning(f"No matching records found for Rule {rule_id}. Skipping.")
            continue

        # === Apply condition ===
        if rule_type == "dependent":
            df_other = df_config.select("MG_id", "salesforce_setting_name", "salesforce_setting_value") \
                .withColumnRenamed("salesforce_setting_name", "cond_field") \
                .withColumnRenamed("salesforce_setting_value", "cond_value")

            try:
                df_joined = (
                    df_target.alias("t")
                    .join(df_other.alias("c"), on="MG_id")
                    .filter(expr(condition.replace("salesforce_setting_name", "cond_field")
                                         .replace("salesforce_setting_value", "cond_value")))
                )
                joined_count = df_joined.count()
                logger.info(f"Records after join + condition: {joined_count}")
                if joined_count == 0:
                    logger.warning(f"Condition '{condition}' for rule {rule_id} yielded no matches.")
                df_filtered = df_joined.select("t.*")
            except Exception as e:
                logger.warning(f"Failed to apply condition '{condition}' for rule {rule_id}: {e}")
                continue
        else:
            df_filtered = df_target
            if condition:
                try:
                    df_filtered = df_filtered.filter(expr(condition))
                    filtered_count = df_filtered.count()
                    logger.info(f"Records after condition filter: {filtered_count}")
                    if filtered_count == 0:
                        logger.warning(f"Condition '{condition}' for rule {rule_id} yielded no matches.")
                except Exception as e:
                    logger.warning(f"Failed to apply condition '{condition}' for rule {rule_id}: {e}")
                    continue

        # === Build PASS/FAIL logic ===
        if expected_value.upper() == "NOT NULL":
            pass_expr = "salesforce_setting_value IS NOT NULL AND salesforce_setting_value != ''"
        elif comparison_operator.upper() == "BETWEEN":
            try:
                lower, upper = expected_value.split("AND")
                pass_expr = f"CAST(salesforce_setting_value AS DOUBLE) BETWEEN {lower.strip()} AND {upper.strip()}"
            except ValueError:
                logger.warning(f"Invalid BETWEEN value in rule {rule_id}: {expected_value}. Skipping.")
                continue
        elif comparison_operator.upper() in ["IN", "NOT IN"]:
            values = ", ".join(f"'{v.strip()}'" for v in expected_value.split(","))
            pass_expr = f"salesforce_setting_value {comparison_operator.upper()} ({values})"
        else:
            pass_expr = f"salesforce_setting_value {comparison_operator} '{expected_value}'"

        logger.info(f"Pass/Fail expression: {pass_expr}")

        df_result = (
            df_filtered
            .withColumn("rule_id", lit(rule_id))
            .withColumn("rule_name", lit(rule_name))
            .withColumn("expected_value", lit(expected_value))
            .withColumn("comparison_operator", lit(comparison_operator))
            .withColumn("pass_fail", expr(f"CASE WHEN {pass_expr} THEN 'PASS' ELSE 'FAIL' END"))
            .withColumnRenamed("salesforce_setting_name", "field_name")
            .withColumnRenamed("salesforce_setting_value", "actual_value")
            .withColumn("client_id", lit(client_id))
            .withColumn("system", lit(system))
            .select("system", "client_id", "MG_id", "field_name", "actual_value", "expected_value",
                    "comparison_operator", "pass_fail", "rule_id", "rule_name")
        )

        result_count = df_result.count()
        logger.info(f"Rule {rule_id} → Result rows: {result_count}")

        results.append(df_result)

    if results:
        df_final = results[0]
        for df in results[1:]:
            df_final = df_final.unionByName(df)
        logger.info(f"Total rows in final result: {df_final.count()}")
        return df_final
    else:
        logger.warning("No rule evaluations produced results.")
        return spark.createDataFrame([], schema="""
            system STRING,
            client_id STRING,
            MG_id STRING,
            field_name STRING,
            actual_value STRING,
            expected_value STRING,
            comparison_operator STRING,
            pass_fail STRING,
            rule_id STRING,
            rule_name STRING
        """)


# === APPLY RULES ===
df_results = evaluate_rules_long(df_config, rules)

logger.info(f"Writing evaluation results to: {OUTPUT_PATH}")
df_results.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save(OUTPUT_PATH)
logger.info("Validation completed successfully.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
