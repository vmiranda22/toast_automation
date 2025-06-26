# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

%run ./toast_nb_utils_workfront_sanitize_datetime_string

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_timestamp, count
from pyspark.sql.types import StringType, TimestampType
import logging
import re

logger = logging.getLogger(__name__)

def standardize_workfront_timestamps(
    df: DataFrame,
    columns_to_check: list,
    cleaned_schema: dict = None,
    sample_size: int = 1000
) -> DataFrame:
    """
    Attempts to convert columns to TimestampType based on schema or pattern.

    Applies a sanitization UDF for Workfront-style timestamps (colon before milliseconds),
    then casts the string to Spark's TimestampType. If `cleaned_schema` indicates a timestamp,
    cast is enforced. Otherwise, a pattern match ratio of ≥90% is required.

    Args:
        df (DataFrame): Input Spark DataFrame.
        columns_to_check (list): Column names to inspect.
        cleaned_schema (dict): Optional cleaned schema for forced types.
        sample_size (int): Sample size for inferring timestamp format.

    Returns:
        DataFrame: Updated DataFrame with timestamp columns where applicable.
    """
    if not columns_to_check:
        logger.info("No columns provided for timestamp evaluation.")
        return df

    sample_df = df.limit(sample_size)

    for col_name in columns_to_check:
        if col_name not in df.columns or not isinstance(df.schema[col_name].dataType, StringType):
            continue

        try:
            expected_type = cleaned_schema.get(col_name) if cleaned_schema else None

            # === Force cast based on schema ===
            if isinstance(expected_type, TimestampType):
                logger.info(f"[{col_name}] Force-casting to TimestampType based on cleaned schema.")
                df = df.withColumn(col_name, sanitize_ts_udf(col(col_name)))
                df = df.withColumn(col_name, to_timestamp(col(col_name), "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"))

            else:
                # === Pattern inference ===
                sample_vals = [
                    row[col_name] for row in sample_df.select(col(col_name)).na.drop().collect()
                    if isinstance(row[col_name], str)
                ]

                pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}:\d{3}(Z|[+-]\d{4})?"
                match_ratio = sum(bool(re.match(pattern, v)) for v in sample_vals) / max(len(sample_vals), 1)

                logger.info(f"[{col_name}] Timestamp match ratio: {match_ratio:.2f}")

                if match_ratio >= 0.9:
                    logger.info(f"[{col_name}] Applying sanitization and casting to TimestampType.")
                    df = df.withColumn(col_name, sanitize_ts_udf(col(col_name)))
                    df = df.withColumn(col_name, to_timestamp(col(col_name), "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"))
                else:
                    logger.info(f"[{col_name}] Rejected from TimestampType conversion (match ratio: {match_ratio:.2f})")
                    continue

            # === Log results ===
            counts = df.select(
                count(when(col(col_name).isNotNull(), 1)).alias("non_nulls"),
                count(when(col(col_name).isNull(), 1)).alias("nulls")
            ).collect()[0]

            example = df.filter(col(col_name).isNotNull()).select(col_name).limit(1).collect()
            example_str = example[0][0] if example else "None"

            logger.info(f"[{col_name}] Cast complete: {counts['non_nulls']} non-null, {counts['nulls']} nulls.")
            logger.info(f"[{col_name}] Example casted value: {example_str}")

        except Exception as e:
            logger.warning(f"[{col_name}] Failed during timestamp evaluation: {e}", exc_info=True)

    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
