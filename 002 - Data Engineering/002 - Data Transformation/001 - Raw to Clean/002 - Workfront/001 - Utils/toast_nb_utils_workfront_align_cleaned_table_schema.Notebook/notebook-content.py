# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

from pyspark.sql.types import StructType
from pyspark.sql.functions import lit, col
import logging

PYSPARK_TO_SQL_TYPES = {
    "StringType": "STRING",
    "IntegerType": "INT",
    "BooleanType": "BOOLEAN",
    "TimestampType": "TIMESTAMP",
    "DoubleType": "DOUBLE"
}

def align_cleaned_table_schema(
    spark,
    df,
    delta_table_path: str,
    logger=None,
    evolve_delta_schema: bool = True
):
    """
    Aligns a cleaned DataFrame with an existing Delta table schema.

    Preserves inferred types from the cleaned DataFrame.
    Only adds missing columns (in Delta or in DataFrame).
    Does NOT cast cleaned DataFrame types to match disk — trust cleaned types instead.

    Returns:
        DataFrame: Reordered and completed DataFrame, preserving inferred types.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        delta_df = spark.read.format("delta").load(delta_table_path)
        delta_schema: StructType = delta_df.schema
        delta_columns = {field.name: field.dataType for field in delta_schema}
        logger.info(f"[CleanedAlign] Loaded Delta schema with {len(delta_columns)} columns.")
    except Exception as e:
        logger.warning(f"[CleanedAlign] Could not read existing Delta table at {delta_table_path}. Returning original DataFrame. Error: {e}")
        return df

    df_columns = {f.name: f.dataType for f in df.schema}

    # === Add missing columns to Delta table (if enabled) ===
    missing_in_delta = {name: dtype for name, dtype in df_columns.items() if name not in delta_columns}
    if evolve_delta_schema and missing_in_delta:
        for name, dtype in missing_in_delta.items():
            pyspark_type_name = type(dtype).__name__
            spark_type = PYSPARK_TO_SQL_TYPES.get(pyspark_type_name, "STRING")
            try:
                spark.sql(f"ALTER TABLE delta.`{delta_table_path}` ADD COLUMNS ({name} {spark_type})")
                logger.info(f"[CleanedAlign] Added column '{name}' ({spark_type}) to Delta table.")
            except Exception as e:
                logger.error(f"[CleanedAlign] Failed to add column '{name}' to Delta: {e}")
    elif missing_in_delta:
        logger.info(f"[CleanedAlign] Skipped adding columns to Delta table (evolve disabled).")

    # === Add missing columns to DataFrame ===
    missing_in_df = set(delta_columns.keys()) - set(df_columns.keys())
    for name in missing_in_df:
        logger.info(f"[CleanedAlign] Adding missing column '{name}' to DataFrame with type {delta_columns[name]}.")
        df = df.withColumn(name, lit(None).cast(delta_columns[name]))

    # === Reorder only (NO TYPE CASTING) ===
    ordered_columns = [field.name for field in delta_schema if field.name in df.columns]
    extra_columns = [c for c in df.columns if c not in ordered_columns]
    df = df.select(*ordered_columns, *extra_columns)
    logger.info(f"[CleanedAlign] Reordered DataFrame columns (preserving cleaned types).")

    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
