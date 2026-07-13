"""
Loads raw Olist data into the bronze schema in PostgreSQL (typed as TEXT). FastAPI source: TABLE_MAP and extract_from_api().
NOT clean, cast, join, or interpret data. Any transformation belongs in dbt staging models (silver).
"""

import csv
import hashlib  # hash for geolocation table
import logging
import sys
import time
import requests
from pathlib import Path

from typing import Iterator

# To use TABLE_MAP
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pg_load import get_connection, load_table, verify_load  # noqa: E402
from shared.table_map import TABLE_MAP  # noqa: E402 # Shared table metadata

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
API_BASE_URL = "http://127.0.0.1:8000"

logger = logging.getLogger("bronze_load")


# Ingest from FastApi
def extract_from_api(
    table_name: str,
    compute_row_hash: bool = False,
    columns: list[str] | None = None,
    page_size: int = 1000,
) -> Iterator[dict]:
    # Fetch a table from the FastAPI service, page by page, yielding one dict per row.
    page = 1
    while True:
        response = requests.get(
            f"{API_BASE_URL}/{table_name}",
            params={"page": page, "size": page_size},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        for row in payload["data"]:
            if compute_row_hash:
                if columns is None:
                    raise ValueError("columns is required when compute_row_hash=True")
                raw = "|".join(str(row[col]) for col in columns)
                row["_row_hash"] = hashlib.md5(raw.encode("utf-8")).hexdigest()
            yield row

        if page >= payload["total_pages"]:
            break
        page += 1


# kept for reference and local testing. Production ingestion now uses extract_from_api(), same output (Iterator[dict]), different source
def extract_from_csv(
    file_path: Path,
    columns: list[str],
    compute_row_hash: bool = False,
) -> Iterator[dict]:
    # Read a CSV file and yield one dict per row, keyed by columns.
    # Compute_row_hash: Geolocation, key computed from the row's own column values.
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    with file_path.open(
        "r", encoding="utf-8-sig"
    ) as f:  # product_category_name_translation
        reader = csv.DictReader(f)

        missing = set(columns) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{file_path.name} is missing columns: {missing}")

        for row in reader:
            if compute_row_hash:
                raw = "|".join(str(row[col]) for col in columns)
                row["_row_hash"] = hashlib.md5(raw.encode("utf-8")).hexdigest()
            yield row


def main() -> None:
    start_time = time.time()
    logger.info("Starting bronze load - source: FastAPI (%s)", API_BASE_URL)

    conn = get_connection()
    summary: dict[str, int] = {}
    failed_tables: list[str] = []

    try:
        for table_name, config in TABLE_MAP.items():
            # file_path = DATA_DIR / config["file"]
            try:
                logger.info("Extracting %s from %s", table_name, config["file"])

                needs_hash = config.get("hash", False)
                records = extract_from_api(
                    table_name,
                    compute_row_hash=needs_hash,
                    columns=config["columns"],
                )

                insert_columns = (
                    config["columns"] + ["_row_hash"]
                    if needs_hash
                    else config["columns"]
                )
                before_count = verify_load(conn, "bronze", table_name)

                inserted = load_table(
                    conn,
                    schema="bronze",
                    table_name=table_name,
                    columns=insert_columns,
                    conflict_key=config["conflict_key"],
                    records=records,
                )
                after_count = verify_load(conn, "bronze", table_name)
                new_rows = after_count - before_count
                skipped = inserted - new_rows
                summary[table_name] = after_count
                logger.info(
                    "Loaded bronze.%s - %d attempted, %d new, %d skipped (duplicates), %d total rows",
                    table_name,
                    inserted,
                    new_rows,
                    skipped,
                    after_count,
                )

            except Exception as exc:
                conn.rollback()
                failed_tables.append(table_name)
                logger.error("Failed to load bronze.%s: %s", table_name, exc)

    finally:
        conn.close()
        logger.info("Connection closed")

    elapsed = time.time() - start_time
    logger.info("--- BRONZE LOAD SUMMARY ---")
    for table_name, row_count in summary.items():
        logger.info("%s %d rows", table_name, row_count)
    if failed_tables:
        logger.error("Failed tables: %s", ", ".join(failed_tables))
    logger.info("Completed in %.2f seconds", elapsed)

    if failed_tables:
        sys.exit(1)


if __name__ == "__main__":
    main()
