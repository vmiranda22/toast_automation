# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

import requests
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def fetch_workfront_data(
    url: str,
    params: Dict[str, Any],
    limit: int = 100,
    retries: int = 3,
    timeout: int = 10,
    max_pages: int = None,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Fetches paginated data from the Workfront API using Workfront’s specific pagination model:
    - $$FIRST: Offset index for the first record to return
    - $$LIMIT: Number of records to return per page

    This function is designed specifically for the Workfront API and is not intended for general REST APIs.

    Args:
        url (str): Full Workfront API endpoint (e.g., https://.../project/search).
        params (Dict[str, Any]): Query parameters including filters and fields.
        limit (int): Number of records per API call (default: 100).
        retries (int): Number of retry attempts for failed requests (default: 3).
        timeout (int): Timeout in seconds for each request (default: 10).
        max_pages (int, optional): Maximum number of pages to retrieve. Useful for testing or limiting scope.
        verbose (bool): If True, logs each page fetch and summary messages.

    Returns:
        List[Dict[str, Any]]: Aggregated list of all records returned by the API.
    """
    data = []           # Final result list of all records.
    offset = 0          # Workfront API pagination offset.
    page_count = 0      # Tracks number of pages retrieved.

    while True:
        current = params.copy()  # Avoid mutating the original params dict.
        current["$$FIRST"] = offset
        current["$$LIMIT"] = limit

        for attempt in range(retries):  # Retry logic with exponential backoff.
            try:
                res = requests.get(url, params=current, timeout=timeout)
                res.raise_for_status()  # Raise HTTPError for bad responses.

                page = res.json().get("data", [])
                if not page:
                    if verbose:
                        logger.info(f"[Workfront] No more data returned at offset {offset}.")
                    return data  # No more data; exit loop.

                data.extend(page)
                offset += limit
                page_count += 1

                if verbose:
                    logger.info(f"[Workfront] Fetched page {page_count} (offset {offset}). "
                                f"Total records so far: {len(data)}.")

                if max_pages and page_count >= max_pages:
                    if verbose:
                        logger.warning(f"[Workfront] Reached max_pages limit: {max_pages}.")
                    return data

                break  # Exit retry loop on success.

            except requests.RequestException as e:
                if attempt < retries - 1:
                    wait = 2 ** attempt  # Exponential backoff.
                    logger.warning(f"[Workfront] Retry {attempt + 1}/{retries} after error: {e}. "
                                   f"Waiting {wait}s.")
                    time.sleep(wait)
                else:
                    logger.error(f"[Workfront] API error at offset {offset}: {e}")
                    return data  # Exit and return what we have.

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
