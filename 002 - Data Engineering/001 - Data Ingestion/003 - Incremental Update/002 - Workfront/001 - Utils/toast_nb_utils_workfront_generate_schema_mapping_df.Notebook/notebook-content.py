# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

from datetime import datetime
from hashlib import md5
from typing import Dict
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, BooleanType, TimestampType
from pyspark.sql import Row


def generate_schema_mapping_df(
    spark: SparkSession,
    object_type: str,
    raw_to_sanitized: Dict[str, str]
):
    """
    Builds a Spark DataFrame for auditing Workfront field name transformations.

    Args:
        spark (SparkSession): Active Spark session.
        object_type (str): The Workfront object type (e.g., 'project', 'task').
        raw_to_sanitized (Dict[str, str]): Mapping of raw to sanitized field names.

    Returns:
        Spark DataFrame with columns:
            - object_type: Type of object (e.g., 'project').
            - raw_field: Original field name as received from the API.
            - sanitized_field: Delta Lake-safe field name.
            - detected_at: UTC timestamp when the schema was detected.
            - is_new_field: Always True for this snapshot; helps with dedup logic in downstream use.
            - schema_version: MD5 hash signature representing this exact schema version.
    """
    now = datetime.utcnow()

    # Convert mapping into a sorted list of "raw→sanitized" strings to generate a stable schema signature.
    field_pairs = [(raw, sanitized) for raw, sanitized in raw_to_sanitized.items()]
    sorted_pairs = sorted(f"{raw}→{sanitized}" for raw, sanitized in field_pairs)

    # Concatenate and hash the signature to create a schema version fingerprint.
    schema_signature = "|".join(sorted_pairs)
    schema_version = md5(schema_signature.encode("utf-8")).hexdigest()

    # Create structured rows for each mapping entry.
    rows = [
        Row(
            object_type=object_type,
            raw_field=raw,
            sanitized_field=sanitized,
            detected_at=now,
            is_new_field=True,  # All fields are flagged as new for this run.
            schema_version=schema_version
        )
        for raw, sanitized in raw_to_sanitized.items()
    ]

    # Define the explicit schema for the mapping DataFrame.
    schema = StructType([
        StructField("object_type", StringType(), True),
        StructField("raw_field", StringType(), True),
        StructField("sanitized_field", StringType(), True),
        StructField("detected_at", TimestampType(), True),
        StructField("is_new_field", BooleanType(), True),
        StructField("schema_version", StringType(), True),
    ])

    return spark.createDataFrame(rows, schema=schema)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
