"""
Loads raw Olist data into the bronze schema in PostgreSQL (typed as TEXT). CSV/Olist source: TABLE_MAP and extract_from_csv().
NOT clean, cast, join, or interpret data. Any transformation belongs in dbt staging models (silver).
"""

import csv
import hashlib  # hash for geolocation table
import logging
import sys
import time
from pathlib import Path
from typing import Iterator

from pg_load import get_connection, load_table, verify_load

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Maps bronze table name -> source file, ordered column list, and conflict key. Column order MUST match the CSV header order.
TABLE_MAP: dict[str, dict] = {
    "customers": {
        "file": "olist_customers_dataset.csv",
        "columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
        "conflict_key": "(customer_id)",
        "hash": False,
    },
    "orders": {
        "file": "olist_orders_dataset.csv",
        "columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "conflict_key": "(order_id)",
        "hash": False,
    },
    "order_items": {
        "file": "olist_order_items_dataset.csv",
        "columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
        "conflict_key": "(order_id, order_item_id)",
        "hash": False,
    },
    "order_payments": {
        "file": "olist_order_payments_dataset.csv",
        "columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
        "conflict_key": "(order_id, payment_sequential)",
        "hash": False,
    },
    "order_reviews": {
        "file": "olist_order_reviews_dataset.csv",
        "columns": [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
        "conflict_key": "(review_id, order_id)",
        "hash": False,
    },
    "products": {
        "file": "olist_products_dataset.csv",
        "columns": [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
        "conflict_key": "(product_id)",
        "hash": False,
    },
    "sellers": {
        "file": "olist_sellers_dataset.csv",
        "columns": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
        "conflict_key": "(seller_id)",
        "hash": False,
    },
    "geolocation": {
        "file": "olist_geolocation_dataset.csv",
        "columns": [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
        "conflict_key": "(_row_hash)",
        "hash": True,
    },
    "product_category_name_translation": {
        "file": "product_category_name_translation.csv",
        "columns": [
            "product_category_name",
            "product_category_name_english",
        ],
        "conflict_key": "(product_category_name)",
        "hash": False,
    },
}

logger = logging.getLogger("bronze_load")


# Extraction layer
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


# Orchestration
def main() -> None:
    start_time = time.time()
    logger.info("Starting bronze load - source: local CSV (%s)", DATA_DIR)

    conn = get_connection()
    summary: dict[str, int] = {}
    failed_tables: list[str] = []

    try:
        for table_name, config in TABLE_MAP.items():
            file_path = DATA_DIR / config["file"]
            try:
                logger.info("Extracting %s from %s", table_name, config["file"])

                needs_hash = config.get("hash", False)
                records = extract_from_csv(
                    file_path,
                    config["columns"],
                    compute_row_hash=needs_hash,
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
