# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

from pyspark.sql.functions import lit
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from pyspark.sql import Row
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)

def ensure_schema_drift_table_exists(spark, table_name="schema_drift_signatures", logger=None):
    """
    Ensures that the Delta table used for tracking schema drift exists.

    If the table does not exist, it will be created with the expected schema.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Define schema for schema drift logging table.
    schema = StructType([
        StructField("source_type", StringType(), True),   # Source of the data, e.g., 'workfront'.
        StructField("table_path", StringType(), True),    # Path to the Delta table.
        StructField("schema_hash", StringType(), True),   # MD5 hash of schema structure.
        StructField("run_id", StringType(), True),        # Run identifier (timestamp or job id).
        StructField("logged_at", TimestampType(), True),  # When the schema was logged.
    ])

    try:
        spark.read.table(table_name)
        logger.info(f"[SchemaAlign] Drift tracking table already exists: {table_name}")
    except Exception:
        logger.warning(f"[SchemaAlign] Creating drift tracking table: {table_name}")
        empty_df = spark.createDataFrame([], schema)
        empty_df.write.format("delta").saveAsTable(table_name)

def compute_schema_md5(schema_fields: dict) -> str:
    """
    Computes an MD5 hash from a dictionary of {column_name: data_type}.

    This provides a consistent schema signature for comparison across runs.
    """
    sorted_items = sorted(schema_fields.items())
    serialized = "|".join(f"{k}:{str(v)}" for k, v in sorted_items)
    return hashlib.md5(serialized.encode("utf-8")).hexdigest()

def log_schema_signature(
    spark,
    table_path: str,
    schema_hash: str,
    source_type: str = "workfront",
    run_id: str = None
):
    """
    Logs the computed schema hash to the schema_drift_signatures table for auditing.

    Args:
        spark (SparkSession): Active Spark session.
        table_path (str): Path to the Delta table being tracked.
        schema_hash (str): The MD5 hash of the schema.
        source_type (str): Source system name.
        run_id (str): Optional identifier for the run; defaults to UTC timestamp.
    """
    schema = StructType([
        StructField("source_type", StringType(), True),
        StructField("table_path", StringType(), True),
        StructField("schema_hash", StringType(), True),
        StructField("run_id", StringType(), True),
        StructField("logged_at", TimestampType(), True),
    ])

    row = Row(
        source_type=source_type,
        table_path=table_path,
        schema_hash=schema_hash,
        run_id=run_id or datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        logged_at=datetime.utcnow()
    )

    df_log = spark.createDataFrame([row], schema=schema)
    df_log.write.mode("append").format("delta").option("mergeSchema", "true").saveAsTable("schema_drift_signatures")

def align_table_schema_before_merge(
    spark,
    df,
    delta_table_path: str,
    logger=None,
    evolve_delta_schema: bool = False
):
    """
    Aligns the schema of an incoming DataFrame with the existing Delta table schema.

    Key behaviors:
    - Adds columns that exist in the Delta table but are missing in the DataFrame,
      using the correct data type from the Delta table (not just STRING).
    - Optionally evolves the Delta table to include new columns found in the DataFrame
      but not yet present in the Delta table (added as STRING).
    - Retains all existing columns from the Delta table in the resulting DataFrame,
      ensuring full schema compatibility.
    - Logs schema hash fingerprints to the `schema_drift_signatures` table for auditing
      and drift detection.

    Args:
        spark (SparkSession): Active Spark session.
        df (DataFrame): Incoming DataFrame to align.
        delta_table_path (str): Path to the Delta table.
        logger (Logger, optional): Logger for logging messages.
        evolve_delta_schema (bool): If True, adds new columns from the DataFrame to the Delta table.

    Returns:
        DataFrame: Schema-aligned DataFrame, safe to use in downstream merge operations.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        delta_schema = spark.read.format("delta").load(delta_table_path).schema
        delta_columns = {field.name for field in delta_schema}
        delta_schema_map = {field.name: field.dataType for field in delta_schema}
    except Exception as e:
        logger.warning(f"[SchemaAlign] Could not load Delta schema at {delta_table_path}. Skipping alignment. Error: {e}")
        return df

    incoming_columns = set(df.columns)
    incoming_schema_map = {f.name: f.dataType for f in df.schema}

    # === Compute Schema Hashes for Drift Detection ===
    def stringify_schema(schema_map):
        return {k: str(v) for k, v in schema_map.items()}

    incoming_hash = compute_schema_md5(stringify_schema(incoming_schema_map))
    delta_hash = compute_schema_md5(stringify_schema(delta_schema_map))

    if incoming_hash == delta_hash:
        logger.info(f"[SchemaAlign] Schema unchanged (hash={incoming_hash}) for table: {delta_table_path}")
    else:
        logger.warning(f"[SchemaAlign] Schema change detected (incoming={incoming_hash}, delta={delta_hash}) for table: {delta_table_path}")

    log_schema_signature(
        spark,
        table_path=delta_table_path,
        schema_hash=incoming_hash,
        source_type="workfront"
    )

    # === STEP 1: Add Columns Missing in Incoming DataFrame ===
    missing_in_df = delta_columns - incoming_columns
    if missing_in_df:
        logger.info(f"[SchemaAlign] Adding missing columns to DataFrame: {list(missing_in_df)}")
        for name in missing_in_df:
            dtype = delta_schema_map[name]
            df = df.withColumn(name, lit(None).cast(dtype))
    else:
        logger.info(f"[SchemaAlign] No missing columns to add to DataFrame.")

    # === STEP 2: Evolve Delta Table with New Columns ===
    if evolve_delta_schema:
        missing_in_delta = incoming_columns - delta_columns
        if missing_in_delta:
            logger.warning(f"[SchemaAlign] Evolving Delta table with new columns: {list(missing_in_delta)}")
            for name in missing_in_delta:
                try:
                    spark.sql(f"ALTER TABLE delta.`{delta_table_path}` ADD COLUMNS ({name} STRING)")
                    logger.info(f"[SchemaAlign] Added column '{name}' as STRING to Delta table.")
                except Exception as e:
                    logger.error(f"[SchemaAlign] Failed to add column '{name}' to Delta table: {e}")
        else:
            logger.info(f"[SchemaAlign] No new columns to evolve in Delta table.")

    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
