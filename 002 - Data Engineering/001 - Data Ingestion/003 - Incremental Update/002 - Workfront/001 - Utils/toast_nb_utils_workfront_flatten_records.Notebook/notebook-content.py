# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

import re
from typing import List, Dict, Any, Tuple
from pyspark.sql import SparkSession, Row
from pyspark.sql.types import StructType, StructField, StringType
import pandas as pd

def fallback_sanitize(field: str) -> str:
    """
    Sanitizes a field name for Delta Lake compatibility:
    - Converts to lowercase.
    - Replaces non-alphanumeric characters with underscores.
    - Strips leading/trailing underscores.
    - Collapses multiple underscores into one.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", field.lower()).strip("_")
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized

def flatten_record(record: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """
    Recursively flattens a nested JSON record into a flat dictionary using a separator for key paths.
    
    - Nested keys are concatenated with `sep` (default: "_").
    - All values are converted to strings for consistent typing (or None if null).
    - Field names are sanitized using `fallback_sanitize`.

    Args:
        record (dict): A single JSON-like record (e.g., from Workfront API).
        parent_key (str): Used internally for recursive prefixing.
        sep (str): Separator between parent and child keys in nested structures.

    Returns:
        Dict[str, Any]: A flat dictionary with stringified values and sanitized keys.
    """
    items = []
    for k, v in record.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        new_key = fallback_sanitize(new_key)
        if isinstance(v, dict):
            # Recursively flatten nested dicts.
            items.extend(flatten_record(v, new_key, sep).items())
        else:
            # Convert all values to string (or None).
            items.append((new_key, str(v) if v is not None else None))
    return dict(items)

def flatten_records_workfront(
    data: List[Dict[str, Any]],
    return_keys: bool = False,
    return_mapping: bool = False
) -> Tuple[
    List[Dict[str, Any]],
    List[str],
    Dict[str, str],
    Dict[str, str]
]:
    """
    Flattens all Workfront API records and tracks schema details.

    Args:
        data (List[Dict[str, Any]]): Raw Workfront API data records.
        return_keys (bool): If True, return a sorted list of discovered keys.
        return_mapping (bool): If True, return raw→sanitized and sanitized→raw field name mappings.

    Returns:
        Tuple:
            - List of flattened records
            - List of discovered keys (optional)
            - Raw-to-sanitized mapping (optional)
            - Sanitized-to-raw mapping (optional)
    """
    flat_records = []
    discovered_keys = set()
    raw_to_sanitized = {}
    sanitized_to_raw = {}

    for rec in data:
        flat = flatten_record(rec)
        flat_records.append(flat)
        discovered_keys.update(flat.keys())

        # Track top-level field name mappings only.
        for raw in rec.keys():
            sanitized = fallback_sanitize(raw)
            raw_to_sanitized[raw] = sanitized
            sanitized_to_raw[sanitized] = raw

    results = [flat_records]
    if return_keys:
        results.append(sorted(discovered_keys))
    if return_mapping:
        results.extend([raw_to_sanitized, sanitized_to_raw])

    return tuple(results)

def create_flat_dataframe(
    spark: SparkSession,
    records: List[Dict[str, Any]]
):
    """
    Converts a list of flat dictionaries into a Spark DataFrame,
    inferring schema from all discovered keys and setting all types to StringType.

    Args:
        spark (SparkSession): Active Spark session.
        records (List[Dict[str, Any]]): Flattened records from API response.

    Returns:
        DataFrame: Spark DataFrame with all columns as nullable strings.
    """
    all_keys = set()
    for r in records:
        if isinstance(r, dict):
            all_keys.update(r.keys())

    if not all_keys:
        raise ValueError("No valid fields found in any record.")

    # Ensure consistent schema across rows (fill missing fields with None).
    sorted_keys = sorted(all_keys)
    schema = StructType([StructField(k, StringType(), True) for k in sorted_keys])
    padded_rows = [Row(**{k: r.get(k, None) for k in sorted_keys}) for r in records]
    return spark.createDataFrame(padded_rows, schema=schema)

def log_schema_to_table(
    spark: SparkSession,
    object_type: str,
    raw_to_sanitized: Dict[str, str],
    schema_table: str = "workfront_schema_mapping"
):
    """
    Logs the raw-to-sanitized field name mapping to a Delta table for audit/history purposes.

    Args:
        spark (SparkSession): Active Spark session.
        object_type (str): Workfront object type (e.g., 'project').
        raw_to_sanitized (Dict[str, str]): Field mapping to log.
        schema_table (str): Target Delta table name for the mapping.
    """
    df_map = pd.DataFrame([
        {"object_type": object_type, "raw_field": raw, "sanitized_field": sanitized}
        for raw, sanitized in raw_to_sanitized.items()
    ])
    spark_df = spark.createDataFrame(df_map)
    spark_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(schema_table)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
