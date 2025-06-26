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
import logging
from collections import defaultdict
from typing import Tuple, Dict, Set
from pyspark.sql import DataFrame

logger = logging.getLogger(__name__)

def sanitize_column_names_cleaned(
    df: DataFrame,
    max_length: int = 100
) -> Tuple[DataFrame, Dict[str, str]]:
    """
    Sanitizes DataFrame column names for the cleaned layer.

    This function standardizes column names to ensure they are Delta Lake-friendly,
    consistent, and do not exceed a specified length. It ensures uniqueness even
    after sanitization by appending numeric suffixes where needed.

    Rules applied:
    - Converts names to lowercase.
    - Replaces all non-alphanumeric characters with underscores.
    - Truncates to a maximum length (default: 100 characters).
    - Ensures uniqueness by adding numeric suffixes (e.g., _1, _2).
    
    Args:
        df (DataFrame): Input Spark DataFrame whose column names need sanitizing.
        max_length (int): Optional max character length for sanitized names.

    Returns:
        Tuple[DataFrame, Dict[str, str]]:
            - A new DataFrame with sanitized column names.
            - A dictionary mapping raw → sanitized column names.
    """
    used_names: Set[str] = set()
    suffix_counter: Dict[str, int] = defaultdict(int)
    raw_to_sanitized: Dict[str, str] = {}

    # First pass: sanitize names and track duplicates.
    for col_name in df.columns:
        # Replace non-alphanumeric characters with underscores and lowercase the name.
        sanitized = re.sub(r"[^\w]", "_", col_name).lower()
        sanitized = sanitized[:max_length]
        base = sanitized

        # If name already used, add a numeric suffix until it's unique.
        while sanitized in used_names:
            suffix_counter[base] += 1
            suffix = f"_{suffix_counter[base]}"
            sanitized = base[:max_length - len(suffix)] + suffix

        used_names.add(sanitized)
        raw_to_sanitized[col_name] = sanitized

    # Apply renaming to DataFrame.
    for raw, sanitized in raw_to_sanitized.items():
        if raw != sanitized:
            df = df.withColumnRenamed(raw, sanitized)

    return df, raw_to_sanitized

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
