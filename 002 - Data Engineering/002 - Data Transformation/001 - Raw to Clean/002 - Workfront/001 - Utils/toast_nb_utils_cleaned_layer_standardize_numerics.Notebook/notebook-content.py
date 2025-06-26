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
from pyspark.sql.functions import col, trim, count, when
from pyspark.sql.types import StringType, IntegerType, DoubleType
import logging

logger = logging.getLogger(__name__)

def standardize_workfront_numerics(
    df: DataFrame,
    columns_to_check: list,
    cleaned_schema: dict = None,
    sample_size: int = 1000,
    strict: bool = False
) -> DataFrame:
    """
    Converts string columns to IntegerType or DoubleType based on sampled values.
    If cleaned_schema is provided, uses it to force-cast to the expected type.
    """
    if not columns_to_check:
        logger.info("No columns provided for numeric evaluation.")
        return df

    sample_df = df.limit(sample_size)

    def is_integer(s):
        try:
            return float(s).is_integer()
        except:
            return False

    def is_float(s):
        try:
            float(s)
            return True
        except:
            return False

    eligible_cols = [
        c for c in columns_to_check
        if c in df.columns and isinstance(df.schema[c].dataType, StringType)
    ]

    if not eligible_cols:
        logger.info("No eligible string columns found for numeric standardization.")
        return df

    for col_name in eligible_cols:
        try:
            expected_type = cleaned_schema.get(col_name) if cleaned_schema else None

            def log_cast_result(type_name):
                counts = df.select(
                    count(when(col(col_name).isNotNull(), 1)).alias("non_nulls"),
                    count(when(col(col_name).isNull(), 1)).alias("nulls")
                ).collect()[0]
                example = df.filter(col(col_name).isNotNull()).select(col_name).limit(1).collect()
                example_str = example[0][0] if example else "None"
                logger.info(f"[{col_name}] Cast to {type_name}: {counts['non_nulls']} non-null, {counts['nulls']} nulls.")
                logger.info(f"[{col_name}] Example casted value: {example_str}")

            # === Case 1: Cleaned schema override ===
            if isinstance(expected_type, (IntegerType, DoubleType)):
                type_name = "IntegerType" if isinstance(expected_type, IntegerType) else "DoubleType"
                logger.info(f"[{col_name}] Force-casting to {type_name} based on cleaned schema.")
                df = df.withColumn(col_name, col(col_name).cast(expected_type))
                log_cast_result(type_name)
                continue

            # === Case 2: Infer from data ===
            values = (
                sample_df
                .select(trim(col(col_name)).alias("v"))
                .distinct()
                .rdd.flatMap(lambda x: x)
                .filter(lambda x: x is not None and x.strip() != "")
                .collect()
            )

            float_matches = [v for v in values if is_float(v)]
            float_ratio = len(float_matches) / max(1, len(values))
            logger.info(f"[{col_name}] Float match ratio: {float_ratio:.2f}")

            if (strict and float_ratio == 1.0) or (not strict and float_ratio >= 0.9):
                int_matches = [v for v in float_matches if is_integer(v)]
                is_all_integers = len(int_matches) == len(float_matches)
                target_type = IntegerType() if is_all_integers else DoubleType()
                type_name = "IntegerType" if is_all_integers else "DoubleType"

                df = df.withColumn(col_name, col(col_name).cast(target_type))
                logger.info(f"[{col_name}] Inferred and casted to {type_name}.")
                log_cast_result(type_name)

            else:
                logger.info(f"[{col_name}] Rejected from numeric conversion (match ratio: {float_ratio:.2f}).")

        except Exception as e:
            logger.warning(f"[{col_name}] Failed during numeric evaluation: {e}", exc_info=True)

    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
