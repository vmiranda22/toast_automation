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
# META           "id": "858ad52b-f017-4d74-9957-17175dd47103"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

%run ./toast_nb_utils_workfront_fetch_data

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_workfront_flatten_records

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_workfront_align_table_schema_before_merge

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_workfront_generate_schema_mapping_df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%run ./toast_nb_utils_workfront_standardize_timestamps

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""
Workfront Task Ingestion Pipeline - Microsoft Fabric (Delta Lake)

Overview:
---------
This PySpark notebook ingests updated `task` records from the Workfront API,
flattens nested JSON, generates schema mappings, computes row-level hashes for change detection,
splits the data into base and custom structures, and merges it into Delta Lake tables.

The pipeline also:
- Uses a timestamp cursor to fetch only recently updated records.
- Logs and tracks schema changes for audit and drift detection.
- Ensures Delta Lake tables exist and have aligned schemas before writing.
- Updates the ingestion cursor based on the most recent lastUpdateDate value from the API response.

Steps:
------
1. Setup.
2. Fetch the last cursor timestamp for incremental extraction.
3. Call Workfront API with buffered lastUpdateDate.
4. Flatten JSON records and generate schema mappings.
5. Extract and sanitize lastUpdateDate string for cursor update.
6. Split into base and custom DataFrames.
7. Ensure Delta tables exist or create them.
8. Align schema before merge.
9. Verify schema consistency.
10. Merge records into Delta Lake tables.
11. Update the ingestion cursor with the latest processed timestamp.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import sha2, concat_ws, col, current_timestamp
from pyspark.errors import AnalysisException
from datetime import datetime, timedelta
from py4j.protocol import Py4JJavaError
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import pandas as pd
import logging
from collections import defaultdict
from pyspark.sql import Row

# === STEP 1: Setup ===
# Initialize Spark session, logging, and key parameters.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
spark = SparkSession.builder.getOrCreate()
object_type = "task"  # The Workfront object being ingested.
default_start_date = datetime(2025, 1, 1)

# Define paths for Delta tables in Fabric.
workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
lakehouse_id = "858ad52b-f017-4d74-9957-17175dd47103"
lakehouse_base_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/dbo"
cursor_table_name = "workfront_ingestion_cursor"
cursor_table_path = f"{lakehouse_base_path}/{cursor_table_name}"

# === STEP 2: Fetch the last cursor timestamp ===
# Pull the most recent ingestion timestamp for this object type.
# If none exists, fall back to a default start date.
try:
    cursor_df = spark.sql(f"""
        SELECT last_ingested_at 
        FROM workfront_ingestion_cursor 
        WHERE object_type = '{object_type}'
    """)
    last_update = cursor_df.collect()[0][0] if cursor_df.count() > 0 else default_start_date
except Exception:
    last_update = default_start_date

logger.info(f"Fetching tasks updated since: {last_update}")

# === STEP 3: Prepare Workfront API call ===
# Use a 7-day buffer before the cursor timestamp to ensure capture of any late updates.
# Build API request parameters.
buffered_last_update = last_update - timedelta(days=7)
formatted_date = buffered_last_update.strftime('%Y-%m-%dT%H:%M:%S.000Z')
logger.info(f"Using 7-day buffer. Querying updates since: {formatted_date}")

# Construct API request parameters.
params = {
    "apiKey": "al7s4u94ggluu08vnh7atni3p5sagebm",
    "fields": "*,parameterValues",
    "lastUpdateDate": formatted_date,
    "lastUpdateDate_Mod": "gt"
}
url = f"https://teladochealth.my.workfront.com/attask/api/v19.0/{object_type}/search"

# Fetch paginated API results.
data = fetch_workfront_data(
    url=url,
    params=params,
    limit=500,
    retries=3,
    timeout=15,
    verbose=True,
    max_pages=10000
)

# If no data, exit early.
if not data:
    logger.info(f"No new Workfront '{object_type}' records found since {last_update}. Skipping processing.")
else:
    # === STEP 4: Flatten records and generate mappings ===
    # - Flatten nested JSON records into flat column structure.
    # - Build raw-to-sanitized field mappings for drift tracking.
    records, discovered_keys, raw_to_sanitized, sanitized_to_raw = flatten_records_workfront(
        data,
        return_keys=True,
        return_mapping=True
    )
    df_flat = create_flat_dataframe(spark, records)

    # Save raw-to-sanitized field mappings for traceability.
    mapping_df = generate_schema_mapping_df(spark, object_type="task", raw_to_sanitized=raw_to_sanitized)
    mapping_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable("workfront_schema_mapping")

    # Ensure table for schema drift tracking exists and log schema hash.
    ensure_schema_drift_table_exists(spark)
    log_schema_to_table(spark, object_type="task", raw_to_sanitized=raw_to_sanitized)

    # Compute a hash of all columns per row for change detection.
    df_flat = df_flat.withColumn("row_hash", sha2(concat_ws("|", *df_flat.columns), 256))

    # === STEP 5: Extract and sanitize lastUpdateDate for cursor update ===
    # - No timestamp casting for data fields.
    # - Extract max raw string value of lastUpdateDate for cursor update.
    # - Sanitize format using a Python function before casting in Spark.
    last_update_col = raw_to_sanitized.get("lastUpdateDate")

    if last_update_col is None or last_update_col not in df_flat.columns:
        raise ValueError("Could not find 'lastUpdateDate' in sanitized fields. Cannot proceed.")

    # Pull the raw max value as a string (ISO format from Workfront, but needs cleanup).
    last_update_raw = df_flat.selectExpr(f"max({last_update_col}) AS max_ts").collect()[0]["max_ts"]
    logger.info(f"Raw max lastUpdateDate from data: {last_update_raw}")

    # === STEP 6: Split into base/custom DataFrames ===
    # - Custom fields prefixed with 'parametervalues_de_' go to custom table.
    # - Remaining fields (except row_hash/id) go to base table.
    custom_columns = [c for c in df_flat.columns if c.startswith("parametervalues_de_") or c in ["id", "row_hash", last_update_col]]
    base_columns = [c for c in df_flat.columns if not c.startswith("parametervalues_de_")]
    if "id" not in base_columns:
        base_columns.append("id")
    if "id" not in custom_columns:
        custom_columns.append("id")

    # Add timestamp for ingestion tracking.
    df_base = df_flat.select(*base_columns).withColumn("ingested_at", current_timestamp())
    df_custom = df_flat.select(*custom_columns).withColumn("ingested_at", current_timestamp())

    # === STEP 7: Ensure Delta tables exist ===
    # - Create empty Delta tables if they don’t already exist at the expected paths.
    base_table_path = f"{lakehouse_base_path}/workfront_{object_type}_base_raw"
    custom_table_path = f"{lakehouse_base_path}/workfront_{object_type}_custom_raw"

    def ensure_raw_table_exists(spark, df, table_path, logger, label="base"):
        try:
            spark.read.format("delta").load(table_path)
            logger.info(f"raw {label} table already exists at path: {table_path}")
        except (AnalysisException, Py4JJavaError):
            logger.warning(f"raw {label} table does not exist. Creating it at: {table_path}")
            df.limit(0).write.format("delta").option("mergeSchema", "true").save(table_path)

    ensure_raw_table_exists(spark, df_base, base_table_path, logger, "base")
    ensure_raw_table_exists(spark, df_custom, custom_table_path, logger, "custom")

    # === STEP 8: Align schema before merge ===
    # - Align DataFrame schema with existing Delta table schema.
    # - Add missing columns to DataFrame if needed.
    df_custom_aligned = align_table_schema_before_merge(
        spark, df_custom, custom_table_path, logger, evolve_delta_schema=True
    )
    df_custom_aligned.createOrReplaceTempView("staging_custom")

    df_base_aligned = align_table_schema_before_merge(
        spark, df_base, base_table_path, logger, evolve_delta_schema=True
    )
    df_base_aligned.createOrReplaceTempView("staging_base")

    # === STEP 9: Verify schema consistency ===
    # - Check for any columns still missing after alignment.
    # - Raise an error if misalignment persists to avoid bad writes.
    base_schema = spark.read.format("delta").load(base_table_path).columns
    custom_schema = spark.read.format("delta").load(custom_table_path).columns
    if missing := set(df_base_aligned.columns) - set(base_schema):
        raise ValueError(f"Base table schema mismatch: missing columns {missing}")
    if missing := set(df_custom_aligned.columns) - set(custom_schema):
        raise ValueError(f"Custom table schema mismatch: missing columns {missing}")

    # === STEP 10: Merge records into Delta tables ===
    # - Use MERGE with row_hash comparison to perform upserts.
    # - Avoid reprocessing unchanged rows.
    merge_success = True
    try:
        spark.sql(f"""
            MERGE INTO delta.`{base_table_path}` AS target
            USING staging_base AS source
            ON target.id = source.id
            WHEN MATCHED AND target.row_hash != source.row_hash THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)
    except Exception as e:
        logger.error(f"Base merge failed: {e}")
        merge_success = False

    try:
        spark.sql(f"""
            MERGE INTO delta.`{custom_table_path}` AS target
            USING staging_custom AS source
            ON target.id = source.id
            WHEN MATCHED AND target.row_hash != source.row_hash THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)
    except Exception as e:
        logger.error(f"Custom merge failed: {e}")
        merge_success = False

    # === STEP 11: Update the ingestion cursor ===
    # - Sanitize raw lastUpdateDate string.
    # - Cast sanitized value to TimestampType for the cursor table.
    # - Use a MERGE operation to upsert the cursor entry.
    if merge_success:
        # Define the schema for the cursor table.
        empty_cursor_schema = StructType([
            StructField("object_type", StringType(), True),
            StructField("last_ingested_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True)
        ])

        # Create the cursor table if it doesn't exist.
        try:
            spark.read.format("delta").load(cursor_table_path)
        except (Py4JJavaError, AnalysisException):
            empty_cursor_df = spark.createDataFrame([], empty_cursor_schema)
            empty_cursor_df.write.format("delta").save(cursor_table_path)

        # Sanitize the raw Workfront datetime string.
        sanitized = sanitize_workfront_datetime_string(last_update_raw)

        # Define schema with a string column to hold the sanitized datetime.
        cursor_raw_schema = StructType([
            StructField("object_type", StringType(), True),
            StructField("last_ingested_at_str", StringType(), True),
            StructField("updated_at", TimestampType(), True)
        ])

        # Create cursor update DataFrame, convert to TimestampType, and trim to required fields.
        cursor_update = spark.createDataFrame(
            [(object_type, sanitized, datetime.utcnow())],
            schema=cursor_raw_schema
        ).withColumn(
            "last_ingested_at", to_timestamp("last_ingested_at_str")
        ).select(
            "object_type", "last_ingested_at", "updated_at"
        )

        cursor_update.createOrReplaceTempView("cursor_update_view")

        spark.sql(f"""
            MERGE INTO delta.`{cursor_table_path}` AS target
            USING cursor_update_view AS source
            ON target.object_type = source.object_type
            WHEN MATCHED THEN
                UPDATE SET target.last_ingested_at = source.last_ingested_at,
                        target.updated_at = source.updated_at
            WHEN NOT MATCHED THEN
                INSERT (object_type, last_ingested_at, updated_at)
                VALUES (source.object_type, source.last_ingested_at, source.updated_at)
        """)
        logger.info("Ingestion cursor updated.")
    else:
        logger.warning("Skipping cursor update due to failed merge.")

logger.info("Notebook execution completed.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
