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

from typing import List
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_timestamp
import logging

logger = logging.getLogger(__name__)

def standardize_workfront_timestamps(
    df: DataFrame,
    timestamp_columns: List[str],
    verbose: bool = False
) -> DataFrame:
    """
    Parses Workfront-style timestamp strings into TimestampType columns.

    For each given column:
    - Creates `_sanitized_<col>` as cleaned string.
    - Creates `_parsed_<col>` as a true Spark timestamp.

    Args:
        df (DataFrame): Input DataFrame with raw Workfront datetime strings.
        timestamp_columns (List[str]): List of columns to standardize.
        verbose (bool): If True, logs parsing failures.

    Returns:
        DataFrame: Original DataFrame with added `_parsed_` and `_sanitized_` columns.
    """
    for col_name in timestamp_columns:
        if col_name not in df.columns:
            continue

        sanitized_col = f"_sanitized_{col_name}"
        parsed_col = f"_parsed_{col_name}"

        df = df.withColumn(sanitized_col, sanitize_ts_udf(col(col_name)))
        df = df.withColumn(parsed_col, to_timestamp(col(sanitized_col), "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"))

        if verbose:
            failed = df.filter(col(parsed_col).isNull() & col(col_name).isNotNull()).count()
            total = df.filter(col(col_name).isNotNull()).count()
            if failed > 0:
                logger.warning(f"[Workfront] Failed to parse {failed}/{total} values in '{col_name}'.")

    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
