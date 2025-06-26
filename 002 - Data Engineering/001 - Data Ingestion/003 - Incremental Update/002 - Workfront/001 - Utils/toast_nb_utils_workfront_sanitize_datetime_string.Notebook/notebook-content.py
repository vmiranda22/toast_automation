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
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

def sanitize_workfront_datetime_string(dt_string: str) -> str:
    """
    Fixes Workfront timestamp strings to match expected ISO 8601 format.

    Handles:
    - Replaces colon before milliseconds with dot.
    - Converts timezone offset from '+0000' to '+00:00'.
    - Appends 'Z' if no offset present.
    """
    if not isinstance(dt_string, str) or "T" not in dt_string:
        return dt_string

    dt_string = re.sub(r':(\d{2,6})([+-]\d{4})$', r'.\1\2', dt_string)   # :SSSS+0000 → .SSSS+0000
    dt_string = re.sub(r':(\d{2,6})$', r'.\1Z', dt_string)               # :SSSS → .SSSSZ
    dt_string = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', dt_string)      # +0000 → +00:00

    return dt_string

# Register Spark UDF.
sanitize_ts_udf = udf(sanitize_workfront_datetime_string, StringType())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
