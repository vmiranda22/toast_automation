# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

from pyspark.sql import DataFrame
from pyspark.sql.functions import lower, trim, when, col, count
from pyspark.sql.types import StringType, BooleanType
import logging

logger = logging.getLogger(__name__)

BOOLEAN_LIKE_VALUES = {"true", "false", "1", "0", "yes", "no"}

def standardize_workfront_booleans(
    df: DataFrame,
    columns_to_check: list,
    cleaned_schema: dict = None,
    sample_size: int = 1000,
    strict: bool = False
) -> DataFrame:
    """
    Attempts to convert columns to BooleanType based on content or schema.

    This utility supports two modes:
    - Schema-based: If cleaned_schema indicates BooleanType, it forces the cast.
    - Inference-based: Otherwise, it samples distinct values to detect if 90% or more
      match typical boolean-like values ("true", "false", "1", "0", "yes", "no").

    Args:
        df (DataFrame): Input Spark DataFrame.
        columns_to_check (list): Column names to evaluate for boolean casting.
        cleaned_schema (dict): Optional schema map for forced casting.
        sample_size (int): Number of rows to sample for type inference.
        strict (bool): If True, require 100% match to cast. Else, allow ≥90%.

    Returns:
        DataFrame: Updated DataFrame with BooleanType columns where appropriate.
    """
    if not columns_to_check:
        logger.info("No columns provided for boolean evaluation.")
        return df

    sample_df = df.limit(sample_size)

    for col_name in columns_to_check:
        if col_name not in df.columns or not isinstance(df.schema[col_name].dataType, StringType):
            continue

        try:
            raw_type = df.schema[col_name].dataType
            expected_type = cleaned_schema.get(col_name) if cleaned_schema else None

            if isinstance(expected_type, BooleanType):
                logger.info(f"[{col_name}] Raw type is {raw_type}.")
                logger.info(f"[{col_name}] Force-casting to BooleanType based on cleaned schema.")
                df = df.withColumn(
                    col_name,
                    when(lower(trim(col(col_name))).isin("true", "1", "yes"), True)
                    .when(lower(trim(col(col_name))).isin("false", "0", "no"), False)
                    .otherwise(None)
                    .cast(BooleanType())
                )
            else:
                values = (
                    sample_df
                    .select(trim(lower(col(col_name))).alias("v"))
                    .distinct()
                    .rdd.flatMap(lambda x: x)
                    .filter(lambda x: x is not None and x.strip() != "")
                    .collect()
                )

                match_count = sum(v in BOOLEAN_LIKE_VALUES for v in values)
                match_ratio = match_count / max(1, len(values))

                if (strict and match_ratio == 1.0) or (not strict and match_ratio >= 0.9):
                    logger.info(f"[{col_name}] Converting to BooleanType (match ratio: {match_ratio:.2f}).")
                    df = df.withColumn(
                        col_name,
                        when(lower(trim(col(col_name))).isin("true", "1", "yes"), True)
                        .when(lower(trim(col(col_name))).isin("false", "0", "no"), False)
                        .otherwise(None)
                        .cast(BooleanType())
                    )
                else:
                    logger.info(f"[{col_name}] Rejected from BooleanType conversion (match ratio: {match_ratio:.2f}).")
                    continue

            # === Log summary statistics ===
            counts = df.select(
                count(when(col(col_name).isNotNull(), 1)).alias("non_nulls"),
                count(when(col(col_name).isNull(), 1)).alias("nulls")
            ).collect()[0]

            example = df.filter(col(col_name).isNotNull()).select(col_name).limit(1).collect()
            example_str = example[0][0] if example else "None"

            logger.info(f"[{col_name}] Cast complete: {counts['non_nulls']} non-null, {counts['nulls']} nulls.")
            logger.info(f"[{col_name}] Example casted value: {example_str}")

        except Exception as e:
            logger.warning(f"[{col_name}] Failed during boolean evaluation: {e}", exc_info=True)

    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
