# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "858ad52b-f017-4d74-9957-17175dd47103",
# META       "default_lakehouse_name": "toast_lh_workfront_raw",
# META       "default_lakehouse_workspace_id": "b08d383a-b8cc-4b8e-b189-d9d696a01977",
# META       "known_lakehouses": [
# META         {
# META           "id": "19d0a156-0ba5-48d9-ad24-2d55e56083dc"
# META         },
# META         {
# META           "id": "858ad52b-f017-4d74-9957-17175dd47103"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

%run ./toast_nb_utils_workfront_align_cleaned_table_schema

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_cleaned_layer_standardize_timestamps

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_cleaned_layer_sanitize_column_name

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_cleaned_layer_standardize_booleans

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_cleaned_layer_standardize_numerics

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# === IMPORTS ===
from pyspark.sql import SparkSession
from pyspark.sql.utils import AnalysisException
from pyspark.sql.functions import sha2, concat_ws, col, current_timestamp, max as spark_max, to_timestamp, lit, row_number
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, ArrayType
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import logging
import uuid

# === LOGGING SETUP ===
# Configure logger for consistent session-specific tracking.
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
session_id = str(uuid.uuid4())[:8]  # Unique session identifier for traceability.

# === INITIALIZE SPARK SESSION ===
spark = SparkSession.builder.getOrCreate()

# === CONFIGURATION ===
# Define the type of object being processed and Fabric workspace/lakehouse IDs.
object_type = "task"
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
lakehouse_id_raw = "858ad52b-f017-4d74-9957-17175dd47103"
lakehouse_id_cleaned = "19d0a156-0ba5-48d9-ad24-2d55e56083dc"

# === STORAGE PATHS ===
# Define the OneLake paths for raw and cleaned data tables.
raw_base_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_raw}/Tables/dbo/workfront_{object_type}_base_raw"
raw_custom_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_raw}/Tables/dbo/workfront_{object_type}_custom_raw"
cleaned_base_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_cleaned}/Tables/dbo/workfront_{object_type}_base_cleaned"
cleaned_custom_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_cleaned}/Tables/dbo/workfront_{object_type}_custom_cleaned"
cleaned_cursor_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_cleaned}/Tables/dbo/workfront_cleaned_cursor"

# === TRUST TABLE SETUP ===
# Schema and storage path for the schema trust table used for data type validation.
trust_table_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id_cleaned}/Tables/dbo/workfront_schema_trust"
trust_schema = StructType([
    StructField("object_type", StringType(), True),
    StructField("column_name", StringType(), True),
    StructField("data_type", StringType(), True),
    StructField("is_verified", BooleanType(), True),
    StructField("updated_at", TimestampType(), True)
])

# === LOAD CURSOR TIMESTAMP ===
# Load the latest cleaned ingestion timestamp from the cursor table, or use default.
try:
    df_cursor = spark.read.format("delta").load(cleaned_cursor_path).filter(col("object_type") == object_type).select("last_ingested_at")
    last_cleaned_cursor_row = df_cursor.first()
    last_cleaned_cursor = last_cleaned_cursor_row["last_ingested_at"] if last_cleaned_cursor_row and last_cleaned_cursor_row["last_ingested_at"] else datetime(2025, 1, 1)
except Exception:
    logger.warning(f"[{session_id}] No valid cursor found. Defaulting to 2025-01-01.")
    last_cleaned_cursor = datetime(2025, 1, 1)

logger.info(f"[{session_id}] Filtering raw records updated after: {last_cleaned_cursor}")
buffered_cursor = last_cleaned_cursor - timedelta(days=7)  # Include delayed records.
logger.info(f"[{session_id}] Using 7-day buffer. Filtering raw records updated after: {buffered_cursor}")

# === LOAD & FILTER RAW DATA ===
# Clean timestamp and filter raw data based on buffered timestamp.
df_raw_base = (
    spark.read.format("delta").load(raw_base_path)
    .withColumn("lastupdatedate_ts", to_timestamp(sanitize_ts_udf(col("lastupdatedate"))))
    .filter(col("lastupdatedate_ts").isNotNull() & (col("lastupdatedate_ts") > buffered_cursor))
    .drop("lastupdatedate")
    .withColumnRenamed("lastupdatedate_ts", "lastupdatedate")
)

df_raw_custom = (
    spark.read.format("delta").load(raw_custom_path)
    .withColumn("lastupdatedate_ts", to_timestamp(sanitize_ts_udf(col("lastupdatedate"))))
    .filter(col("lastupdatedate_ts").isNotNull() & (col("lastupdatedate_ts") > buffered_cursor))
    .drop("lastupdatedate")
    .withColumnRenamed("lastupdatedate_ts", "lastupdatedate")
)

# === UTILITY FUNCTIONS ===

def deduplicate_by_id_keep_latest(df, timestamp_col="lastupdatedate"):
    """
    Deduplicates the DataFrame by `id`, keeping the latest record based on `timestamp_col`.
    """
    w = Window.partitionBy("id").orderBy(col(timestamp_col).desc(), col("row_hash").desc())
    return df.withColumn("rn", row_number().over(w)).filter(col("rn") == 1).drop("rn")

def promote_verified_types(df_cleaned, object_type, trust_table_path, logger):
    """
    Promotes columns from 'is_verified = False' to 'True' in the schema trust table
    if their data types now match the inferred types in the cleaned DataFrame.

    Args:
        df_cleaned (DataFrame): The cleaned DataFrame with inferred/cast types.
        object_type (str): The type of object (e.g., 'task', 'project').
        trust_table_path (str): Path to the Delta table containing schema trust info.
        logger (Logger): Logger instance for structured logging.
    Note:
        This is a simple matching approach. A more conservative promotion mechanism
        (e.g., requiring multiple consistent inferences over time) will be implemented in the future.
    """
    try:
        # Load all unverified trust entries for the current object type.
        df_trust = spark.read.format("delta").load(trust_table_path).filter(
            (col("object_type") == object_type) & (col("is_verified") == False)
        )

        # Collect column names and proposed data types from trust table.
        df_trust_records = df_trust.select("column_name", "data_type").collect()
        if not df_trust_records:
            logger.info(f"[{session_id}] No unverified types to evaluate for promotion.")
            return

        updates = []
        for row in df_trust_records:
            col_name = row["column_name"]
            target_type = row["data_type"].lower()

            # Only consider columns that exist in the cleaned DataFrame.
            if col_name in df_cleaned.columns:
                # Get the current inferred type from the DataFrame.
                current_type = df_cleaned.schema[col_name].dataType.simpleString().lower()

                # If the inferred type matches the target unverified type, mark for promotion.
                if current_type == target_type:
                    updates.append((object_type, col_name, target_type.upper(), True, datetime.utcnow()))



        if updates:
            # Create DataFrame from updates
            df_updates = spark.createDataFrame(updates, trust_schema)

            # Deduplicate to avoid multiple source rows for the same (object_type, column_name)
            window = Window.partitionBy("object_type", "column_name").orderBy(col("updated_at").desc())
            df_updates = df_updates.withColumn("rn", row_number().over(window)) \
                                .filter(col("rn") == 1).drop("rn")

            df_updates.createOrReplaceTempView("trusted_type_updates")

            # Safe merge
            spark.sql(f"""
                MERGE INTO delta.`{trust_table_path}` AS target
                USING trusted_type_updates AS source
                ON target.object_type = source.object_type AND target.column_name = source.column_name
                WHEN MATCHED THEN UPDATE SET
                    target.is_verified = source.is_verified,
                    target.updated_at = source.updated_at
            """)
            logger.info(f"[{session_id}] Promoted {df_updates.count()} previously unverified types to verified.")

        else:
            logger.info(f"[{session_id}] No trust table promotions needed for object '{object_type}'.")

    except Exception as e:
        logger.error(f"[{session_id}] Failed to promote verified types: {e}", exc_info=True)

# Compare cleaned schema with existing Delta table schema and find mismatches.
def detect_type_mismatches(df_cleaned, delta_path, logger):
    try:
        df_existing = spark.read.format("delta").load(delta_path)
        mismatches = []
        for f in df_cleaned.schema.fields:
            if f.name in df_existing.columns:
                existing_type = dict(df_existing.dtypes)[f.name]
                cleaned_type = f.dataType.simpleString()
                if existing_type != cleaned_type:
                    mismatches.append((f.name, existing_type, cleaned_type))
        return mismatches
    except Exception as e:
        logger.warning(f"[{session_id}] Failed to load existing schema for comparison: {e}")
        return []

# Check if a mismatched type is already verified as safe in the trust table.
def is_verified_type(object_type, column, target_type, trust_table_path):
    try:
        df_trust = spark.read.format("delta").load(trust_table_path)
        row = (
            df_trust.filter((col("object_type") == object_type) &
                            (col("column_name") == column) &
                            (col("data_type") == target_type.upper()) &
                            (col("is_verified") == True))
            .orderBy(col("updated_at").desc())
            .limit(1)
            .collect()
        )
        return bool(row)
    except Exception:
        return False

# Attempt controlled overwrite if all mismatches are verified; else log to trust and skip.
def safe_overwrite_table(df_new, path, object_type, trust_table_path):
    mismatches = detect_type_mismatches(df_new, path, logger)
    verified_and_safe = []
    unverified_records = []

    for col_name, old_type, new_type in mismatches:
        if is_verified_type(object_type, col_name, new_type, trust_table_path):
            logger.info(f"[{session_id}] Type mismatch in '{col_name}' verified as safe ({old_type} → {new_type}).")
            verified_and_safe.append(col_name)
        else:
            logger.warning(f"[{session_id}] Type mismatch in '{col_name}' is NOT verified ({old_type} → {new_type}). Skipping overwrite.")
            unverified_records.append((object_type, col_name, new_type.upper(), False, datetime.utcnow()))

    # Log unverified to trust.
    if unverified_records:
        try:
            df_unverified = spark.createDataFrame(unverified_records, trust_schema)
            df_unverified.createOrReplaceTempView("unverified_schema_records")

            spark.sql(f"""
                MERGE INTO delta.`{trust_table_path}` AS target
                USING unverified_schema_records AS source
                ON target.object_type = source.object_type AND target.column_name = source.column_name
                WHEN MATCHED THEN UPDATE SET
                    target.data_type = source.data_type,
                    target.is_verified = source.is_verified,
                    target.updated_at = source.updated_at
                WHEN NOT MATCHED THEN INSERT *
            """)
            logger.info(f"[{session_id}] Logged {len(unverified_records)} unverified type changes to trust table.")
        except Exception as e:
            logger.error(f"[{session_id}] Failed to log unverified schema changes: {e}", exc_info=True)

        return False

    # OVERWRITE with combined historical + new data.
    if verified_and_safe:
        try:
            df_existing = spark.read.format("delta").load(path)

            # Align columns: add missing/nulls to each
            df_existing_aligned = align_schema_for_overwrite(df_existing, df_new)
            combined = df_existing_aligned.unionByName(df_new, allowMissingColumns=True)
            logger.warning(f"[{session_id}] Performing controlled overwrite with full data merge: {df_existing.count()} existing + {df_new.count()} new")

            combined.write.format("delta") \
                .mode("overwrite") \
                .option("overwriteSchema", "true") \
                .save(path)

            return True
        except Exception as e:
            logger.error(f"[{session_id}] Failed to overwrite table at {path}: {e}", exc_info=True)
            raise

    return False

# Add a SHA-256 row-level hash to help detect changes for upsert logic.
# NOTE:
# We compute a deterministic row-level hash (row fingerprint) based on the content of each record.
# This technique is formally known as **row hashing**, **content-based fingerprinting**, or **hash-based change detection**.
# The goal is to track meaningful changes in data rows for update detection during MERGE operations.
#
# The hash includes all columns except known volatile fields (like `ingested_at`), so any substantive change to
# the row content (e.g., a field update in Workfront) results in a different `row_hash`. This allows us to detect
# when an update is needed without comparing all columns manually.
#
# HOWEVER, this alone is not sufficient: the incoming data may contain multiple versions of the same `id`
# (e.g., repeated records from Workfront due to timestamp delays or reprocessing).
# If not handled, this causes multiple rows with the same `id` to be merged or inserted into the Delta table,
# depending on how the `MERGE` conditions are evaluated.
#
# To address this, we apply **deduplication by business key (`id`)**, retaining only the latest version of each
# record based on a timestamp field (e.g., `lastupdatedate`). This ensures that for each `id`, only the most recent
# and most accurate representation is persisted to the cleaned table.

def add_row_hash(df):
    cols = sorted([c for c in df.columns if c not in {"row_hash", "ingested_at"}])
    return df.withColumn("row_hash", sha2(concat_ws("|", *[col(c) for c in cols]), 256))

# Cast existing Delta schema to match new DataFrame schema before merging.
def align_schema_for_overwrite(df_existing, df_new):
    new_cols = {f.name: f.dataType for f in df_new.schema.fields}
    aligned = df_existing
    for col_name in new_cols:
        if col_name in aligned.columns:
            current_type = aligned.schema[col_name].dataType
            target_type = new_cols[col_name]
            if current_type != target_type:
                aligned = aligned.withColumn(col_name, col(col_name).cast(target_type))
    return aligned.select(df_new.columns)  # ensure same column order

# Merge cleaned table using row_hash logic to detect and update modified rows.
def merge_cleaned_table(df_new, path, view_name, merge_key="id", schema_aligned=True):
    """
    Merges a cleaned DataFrame into a Delta table, using row_hash for change detection.

    Args:
        df_new (DataFrame): Cleaned and aligned data to merge.
        path (str): Delta path to merge into.
        view_name (str): Temporary view name used for SQL MERGE.
        merge_key (str): Primary key to use for deduplication/upserts.
        schema_aligned (bool): If False, performs legacy schema-evolution fallback logic.
    """
    try:
        try:
            df_existing = spark.read.format("delta").load(path)
            logger.info(f"[{session_id}] Target table already exists: {path}")
        except AnalysisException:
            logger.warning(f"[{session_id}] Creating new Delta table at: {path}")
            df_new.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(path)
            return

        # === Optional: fallback schema handling if upstream alignment was skipped ===
        if not schema_aligned and df_existing.schema != df_new.schema:
            logger.warning(f"[{session_id}] Schema mismatch detected and 'schema_aligned' is False. Performing unioned overwrite.")

            existing_casted = df_existing
            for field in df_new.schema.fields:
                if field.name in df_existing.columns:
                    existing_type = df_existing.schema[field.name].dataType
                    if existing_type != field.dataType:
                        logger.warning(f"[{field.name}] Casting from {existing_type} to {field.dataType}")
                        existing_casted = existing_casted.withColumn(
                            field.name, col(field.name).cast(field.dataType)
                        )
                else:
                    logger.info(f"[{field.name}] New column added to schema.")

            # Add any columns that exist in Delta but are missing in df_new.
            missing_cols = [f.name for f in df_existing.schema.fields if f.name not in df_new.columns]
            for col_name in missing_cols:
                df_new = df_new.withColumn(col_name, lit(None).cast(df_existing.schema[col_name].dataType))

            # Union and overwrite with evolved schema.
            df_union = existing_casted.unionByName(df_new, allowMissingColumns=True)
            if not schema_aligned and df_existing.schema != df_new.schema:
                logger.warning(f"[{session_id}] Schema mismatch detected and 'schema_aligned' is False. Performing schema evolution via append.")
                
                df_new.write.format("delta") \
                    .mode("append") \
                    .option("mergeSchema", "true") \
                    .save(path)

                logger.info(f"[{session_id}] Appended data with schema evolution enabled to: {path}")
                return

        # === Perform SQL MERGE ===
        df_new.createOrReplaceTempView(view_name)
        update_set = ",\n    ".join([f"target.{c} = source.{c}" for c in df_new.columns if c != merge_key])
        insert_cols = ", ".join(df_new.columns)
        insert_vals = ", ".join([f"source.{c}" for c in df_new.columns])

        merge_sql = f"""
        MERGE INTO delta.`{path}` AS target
        USING {view_name} AS source
        ON target.{merge_key} = source.{merge_key}
        WHEN MATCHED AND target.row_hash != source.row_hash THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols})
            VALUES ({insert_vals})
        """
        spark.sql(merge_sql)
        logger.info(f"[{session_id}] Merge into {path} completed.")

        # Optionally log final schema.
        final_df = spark.read.format("delta").load(path)
        logger.info(f"[{session_id}] Final schema on disk at {path}:")
        final_df.printSchema()

    except Exception as e:
        logger.error(f"[{session_id}] Failed to merge into {view_name}: {e}", exc_info=True)
        raise

# Clean DataFrame using verified types from the trust table, infer types when needed.
def clean_df_with_trust(df_raw: DataFrame, label: str, object_type: str, trust_table_path: str) -> DataFrame:
    logger.info(f"[{session_id}] Cleaning {label} table using trust-first logic...")

    # Load trust schema.
    try:
        df_trust = spark.read.format("delta").load(trust_table_path)
    except Exception:
        logger.warning(f"[{session_id}] Trust table not found. Creating empty one.")
        empty_trust_df = spark.createDataFrame([], trust_schema)
        empty_trust_df.write.format("delta") \
            .partitionBy("object_type") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .save(trust_table_path)
        df_trust = spark.read.format("delta").load(trust_table_path)

    verified_types = {
        row["column_name"]: row["data_type"]
        for row in df_trust
        .filter((col("object_type") == object_type) & (col("is_verified") == True))
        .select("column_name", "data_type")
        .collect()
    }

    # === STEP 1: Trust-based casting ===
    df = df_raw
    for col_name, data_type in verified_types.items():
        if col_name in df.columns:
            logger.info(f"[{col_name}] Casting to {data_type} based on verified trust.")
            if data_type == "INT":
                df = df.withColumn(col_name, col(col_name).cast("int"))
            elif data_type == "DOUBLE":
                df = df.withColumn(col_name, col(col_name).cast("double"))
            elif data_type == "BOOLEAN":
                df = df.withColumn(col_name, col(col_name).cast("boolean"))
            elif data_type == "TIMESTAMP":
                df = df.withColumn(col_name, col(col_name).cast("timestamp"))

    # Determine which columns were *not* cast.
    inferred_candidates = [
        c for c in df.columns if c not in verified_types and isinstance(df.schema[c].dataType, StringType)
    ]

    logger.info(f"[{session_id}] Inferring types for {len(inferred_candidates)} unverified columns.")

    # === STEP 2: Inference on unverified columns ===
    df = standardize_workfront_timestamps(df, inferred_candidates, sample_size=1000)
    df = standardize_workfront_booleans(df, inferred_candidates, sample_size=1000)
    df = standardize_workfront_numerics(df, inferred_candidates, sample_size=1000)

    # === STEP 3: Clean metadata ===
    df = df.withColumn("ingested_at", current_timestamp())
    df = add_row_hash(df)

    logger.info(f"[{session_id}] {label.capitalize()} table cleaned. Row count: {df.count()}")
    return df

def log_inferred_unverified_columns(df_cleaned, object_type, trust_table_path, logger):
    try:
        df_trust = spark.read.format("delta").load(trust_table_path).filter(
            col("object_type") == object_type
        )
        known_columns = {(row["column_name"], row["data_type"]) for row in df_trust.select("column_name", "data_type").collect()}

        inferred_unverified = []
        for field in df_cleaned.schema.fields:
            col_name = field.name
            data_type = field.dataType.simpleString().upper()

            if (col_name, data_type) not in known_columns:
                inferred_unverified.append((object_type, col_name, data_type, False, datetime.utcnow()))

        if inferred_unverified:
            df_new = spark.createDataFrame(inferred_unverified, trust_schema)
            df_new.write.format("delta").mode("append").save(trust_table_path)
            logger.info(f"[{session_id}] Logged {len(inferred_unverified)} new inferred columns as unverified.")
        else:
            logger.info(f"[{session_id}] No new inferred columns to log.")
    except Exception as e:
        logger.error(f"[{session_id}] Failed to log inferred unverified columns: {e}", exc_info=True)


# === CLEAN BASE TABLE ===
try:
    cleaned_existing_df_base = spark.read.format("delta").load(cleaned_base_path)
    cleaned_schema_base = {f.name: f.dataType for f in cleaned_existing_df_base.schema.fields}
    logger.info(f"[{session_id}] Loaded base cleaned schema with {len(cleaned_schema_base)} fields.")
except Exception as e:
    logger.warning(f"[{session_id}] Failed to load base cleaned schema: {e}")
    cleaned_schema_base = {}

# Full cleaning (casting + inference + metadata).
df_clean_base = clean_df_with_trust(df_raw_base, "base", object_type, trust_table_path)
df_clean_base = deduplicate_by_id_keep_latest(df_clean_base)
df_clean_base = align_cleaned_table_schema(spark, df_clean_base, cleaned_base_path)
log_inferred_unverified_columns(df_clean_base, object_type, trust_table_path, logger)

# === CLEAN CUSTOM TABLE ===
try:
    cleaned_existing_df_custom = spark.read.format("delta").load(cleaned_custom_path)
    cleaned_schema_custom = {f.name: f.dataType for f in cleaned_existing_df_custom.schema.fields}
    logger.info(f"[{session_id}] Loaded custom cleaned schema with {len(cleaned_schema_custom)} fields.")
except Exception as e:
    logger.warning(f"[{session_id}] Failed to load custom cleaned schema: {e}")
    cleaned_schema_custom = {}

df_clean_custom = clean_df_with_trust(df_raw_custom, "custom", object_type, trust_table_path)
df_clean_custom = deduplicate_by_id_keep_latest(df_clean_custom)
df_clean_custom = align_cleaned_table_schema(spark, df_clean_custom, cleaned_custom_path)
log_inferred_unverified_columns(df_clean_custom, object_type, trust_table_path, logger)

# === MERGE OR OVERWRITE CLEANED DATA ===
if not safe_overwrite_table(df_clean_base, cleaned_base_path, object_type, trust_table_path):
    merge_cleaned_table(df_clean_base, cleaned_base_path, "staging_base")

if not safe_overwrite_table(df_clean_custom, cleaned_custom_path, object_type, trust_table_path):
    merge_cleaned_table(df_clean_custom, cleaned_custom_path, "staging_custom")

promote_verified_types(df_clean_base, object_type, trust_table_path, logger)
promote_verified_types(df_clean_custom, object_type, trust_table_path, logger)

# === UPDATE CURSOR TABLE ===
# Persist latest ingestion timestamp for incremental logic in future runs.
try:
    latest_cleaned_ts = df_clean_base.agg(spark_max("lastupdatedate")).collect()[0][0]
    if not latest_cleaned_ts:
        latest_cleaned_ts = datetime.utcnow()

    empty_cursor_schema = StructType([
        StructField("object_type", StringType(), True),
        StructField("last_ingested_at", TimestampType(), True),
        StructField("updated_at", TimestampType(), True)
    ])

    try:
        spark.read.format("delta").load(cleaned_cursor_path)
    except Exception:
        empty_df = spark.createDataFrame([], empty_cursor_schema)
        empty_df.write.format("delta").save(cleaned_cursor_path)

    cursor_update = spark.createDataFrame(
        [(object_type, latest_cleaned_ts, datetime.utcnow())],
        schema=empty_cursor_schema
    )
    cursor_update.createOrReplaceTempView("cursor_update_cleaned")

    spark.sql(f"""
        MERGE INTO delta.`{cleaned_cursor_path}` AS target
        USING cursor_update_cleaned AS source
        ON target.object_type = source.object_type
        WHEN MATCHED THEN UPDATE SET
            target.last_ingested_at = source.last_ingested_at,
            target.updated_at = source.updated_at
        WHEN NOT MATCHED THEN INSERT *
    """)

    logger.info(f"[{session_id}] Cleaned ingestion cursor updated.")
except Exception as e:
    logger.error(f"[{session_id}] Failed to update cleaned cursor: {e}", exc_info=True)
    raise

logger.info(f"[{session_id}] Raw-to-cleaned pipeline for Workfront '{object_type}' completed.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
