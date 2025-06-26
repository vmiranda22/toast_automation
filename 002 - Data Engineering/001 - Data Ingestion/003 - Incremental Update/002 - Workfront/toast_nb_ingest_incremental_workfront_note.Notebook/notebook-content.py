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
Workfront Note Ingestion Pipeline - Microsoft Fabric (Delta Lake)

Overview:
---------
This PySpark notebook ingests updated `note` records from the Workfront API,
flattens nested JSON, generates schema mappings, computes row-level hashes for change detection,
and merges the processed data into a Delta Lake table.

The pipeline also:
- Uses a timestamp cursor to fetch only recently updated records.
- Logs schema changes for audit and drift detection.
- Ensures Delta Lake tables exist and have aligned schemas before writing.
- Updates the ingestion cursor based on the most recent entryDate value in the data.

Steps:
------
1. Setup.
2. Fetch the last ingestion cursor timestamp.
3. Call Workfront API with buffered lastUpdateDate.
4. Flatten API records and generate schema mappings.
5. Extract and sanitize lastUpdateDate for cursor tracking.
6. Ensure Delta table exists and align schema.
7. Merge data into Delta table.
8. Update the ingestion cursor.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import sha2, concat_ws, col, current_timestamp
from pyspark.errors import AnalysisException
from datetime import datetime, timedelta
from py4j.protocol import Py4JJavaError
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import logging

# === STEP 1: Setup ===
# Initialize Spark session, logging, and key parameters.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
spark = SparkSession.builder.getOrCreate()
object_type = "note"
default_start_date = datetime(2025, 1, 1)

workspace_id = "b08d383a-b8cc-4b8e-b189-d9d696a01977"
lakehouse_id = "858ad52b-f017-4d74-9957-17175dd47103"
lakehouse_base_path = f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/dbo"
cursor_table_path = f"{lakehouse_base_path}/workfront_ingestion_cursor"
final_table_path = f"{lakehouse_base_path}/workfront_{object_type}_raw"

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

logger.info(f"Fetching notes updated since: {last_update}")

# === STEP 3: Prepare Workfront API call ===
# Use a 7-day buffer before the cursor timestamp to ensure capture of any late updates.
# Build API request parameters.
buffered_last_update = last_update - timedelta(days=7)
formatted_date = buffered_last_update.strftime('%Y-%m-%dT%H:%M:%S.000Z')
logger.info(f"Using 7-day buffer. Querying updates since: {formatted_date}")

params = {
    "apiKey": "al7s4u94ggluu08vnh7atni3p5sagebm",
    "fields": "*",
    "entryDate": formatted_date,
    "entryDate_Mod": "gt"
}
url = f"https://teladochealth.my.workfront.com/attask/api/v19.0/{object_type}/search"

data = fetch_workfront_data(
    url=url,
    params=params,
    limit=500,
    retries=3,
    timeout=15,
    verbose=True,
    max_pages=10000
)

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

    mapping_df = generate_schema_mapping_df(spark, object_type="note", raw_to_sanitized=raw_to_sanitized)
    mapping_df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable("workfront_schema_mapping")

    ensure_schema_drift_table_exists(spark)
    log_schema_to_table(spark, object_type="note", raw_to_sanitized=raw_to_sanitized)

    df_flat = df_flat.withColumn("row_hash", sha2(concat_ws("|", *df_flat.columns), 256))

    # === STEP 5: Extract and sanitize entryDate for cursor tracking ===
    # - Extract the raw max value from the 'lastUpdateDate' field.
    # - Do not cast during ingestion; only sanitize and convert when updating the cursor.
    last_update_col = raw_to_sanitized.get("entryDate")    
    if last_update_col is None or last_update_col not in df_flat.columns:
        raise ValueError("Could not find 'entryDate' in sanitized fields. Cannot proceed.")

    last_update_raw = df_flat.selectExpr(f"max({last_update_col}) AS max_ts").collect()[0]["max_ts"]
    logger.info(f"Raw max entryDate from data: {last_update_raw}")

    # === STEP 6: Ensure target table exists and align schema ===
    # Add timestamp for ingestion tracking.
    df_final = df_flat.withColumn("ingested_at", current_timestamp())

    # === STEP 7: Ensure Delta tables exist ===
    # - Create empty Delta table if it doesn’t already exist at the expected path.
    def ensure_raw_table_exists(spark, df, table_path, logger, label="raw"):
        try:
            spark.read.format("delta").load(table_path)
            logger.info(f"{label} table already exists at path: {table_path}")
        except (AnalysisException, Py4JJavaError):
            logger.warning(f"{label} table does not exist. Creating it at: {table_path}")
            df.limit(0).write.format("delta").option("mergeSchema", "true").save(table_path)

    ensure_raw_table_exists(spark, df_final, final_table_path, logger, label="note")

    # === STEP 8: Align schema before merge ===
    # - Align DataFrame schema with existing Delta table schema.
    # - Add missing columns to DataFrame if needed.
    df_final_aligned = align_table_schema_before_merge(
        spark, df_final, final_table_path, logger, evolve_delta_schema=True
    )
    df_final_aligned.createOrReplaceTempView("staging_note")

    # === STEP 9: Verify schema consistency ===
    # - Check for any columns still missing after alignment.
    # - Raise an error if misalignment persists to avoid bad writes.
    final_schema = spark.read.format("delta").load(final_table_path).columns
    if missing := set(df_final_aligned.columns) - set(final_schema):
        raise ValueError(f"Note table schema mismatch: missing columns {missing}")

    # === STEP 10: Merge records into Delta Lake table ===
    # - Perform upserts using MERGE, comparing row_hash for change detection.
    # - Skip records that have not changed since the last load.
    merge_success = True
    try:
        spark.sql(f"""
            MERGE INTO delta.`{final_table_path}` AS target
            USING staging_note AS source
            ON target.id = source.id
            WHEN MATCHED AND target.row_hash != source.row_hash THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
        """)
    except Exception as e:
        logger.error(f"[Merge Failure] Note table merge failed: {type(e).__name__} - {str(e)}")
        merge_success = False

    # === STEP 11: Update the ingestion cursor ===
    # - Sanitize the raw Workfront timestamp using a Python function.
    # - Convert the sanitized string to a proper TimestampType.
    # - Use MERGE to insert or update the ingestion cursor table.
    if merge_success:
        empty_cursor_schema = StructType([
            StructField("object_type", StringType(), True),
            StructField("last_ingested_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True)
        ])

        try:
            spark.read.format("delta").load(cursor_table_path)
        except (Py4JJavaError, AnalysisException):
            empty_cursor_df = spark.createDataFrame([], empty_cursor_schema)
            empty_cursor_df.write.format("delta").save(cursor_table_path)

        sanitized = sanitize_workfront_datetime_string(last_update_raw)

        cursor_update = spark.createDataFrame(
            [(object_type, sanitized, datetime.utcnow())],
            schema=StructType([
                StructField("object_type", StringType(), True),
                StructField("last_ingested_at_str", StringType(), True),
                StructField("updated_at", TimestampType(), True)
            ])
        ).withColumn("last_ingested_at", to_timestamp("last_ingested_at_str")) \
         .select("object_type", "last_ingested_at", "updated_at")

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
