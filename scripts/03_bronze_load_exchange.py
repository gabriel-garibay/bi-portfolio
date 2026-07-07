"""
Loads BRL -> EUR daily exchange rates from the Frankfurter API into bronze.exchange_rates.
Frankfurter only publishes rates on business days (Monday-Friday)
"""

import logging
import sys
import time
import pandas as pd
import requests

from pg_load import get_connection, load_table, verify_load

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/{start}..{end}"

BASE_CURRENCY = "BRL"
QUOTE_CURRENCY = "EUR"

TABLE_NAME = "exchange_rates"
COLUMNS = ["rate_date", "base_currency", "quote_currency", "rate"]
CONFLICT_KEY = "(rate_date, base_currency, quote_currency)"

logger = logging.getLogger("exchange_rates_load")


def get_date_range(conn) -> tuple[str, str]:
    # order_purchase_timestamp (price is fixed at purchase time, not at payment approval)
    # order_approved_at also has 160 nulls (raw_exploration.txt).
    # Delivery/estimated-delivery dates are logistics events with no relationship to when the transaction value was determined.
    with conn.cursor() as cur:
        cur.execute(
            "SELECT MIN(order_purchase_timestamp), MAX(order_purchase_timestamp) "  # Real purchase-date range
            "FROM bronze.orders"
        )
        min_date, max_date = cur.fetchone()

    if min_date is None or max_date is None:
        raise ValueError("bronze.orders is empty - run 03_bronze_load_olist.py first")

    # Robust to format variations and delegates to PostgreSQL's datetime parser. Frankfurter expects YYYY-MM-DD format
    return (
        pd.to_datetime(min_date).strftime("%Y-%m-%d"),
        pd.to_datetime(max_date).strftime("%Y-%m-%d"),
    )


def extract_from_frankfurter(start: str, end: str, base: str, quote: str):
    # Once for the full date range and yield one dict per date returned. (Frankfurter supports date ranges natively)
    url = FRANKFURTER_URL.format(start=start, end=end)
    params = {"from": base, "to": quote}

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    for rate_date, rates in data["rates"].items():
        yield {
            "rate_date": rate_date,
            "base_currency": base,
            "quote_currency": quote,
            "rate": str(rates[quote]),
        }


def main() -> None:
    start_time = time.time()
    conn = get_connection()

    try:
        start_date, end_date = get_date_range(conn)
        logger.info(
            "Starting exchange rate load - %s/%s, %s to %s (from bronze.orders)",
            BASE_CURRENCY,
            QUOTE_CURRENCY,
            start_date,
            end_date,
        )
        records = extract_from_frankfurter(
            start_date, end_date, BASE_CURRENCY, QUOTE_CURRENCY
        )
        inserted = load_table(
            conn,
            schema="bronze",
            table_name=TABLE_NAME,
            columns=COLUMNS,
            conflict_key=CONFLICT_KEY,
            records=records,
        )
        total_rows = verify_load(conn, "bronze", TABLE_NAME)
        logger.info(
            "Loaded bronze.%s - %d rows inserted this run, %d total rows in table",
            TABLE_NAME,
            inserted,
            total_rows,
        )
    except Exception as exc:
        conn.rollback()
        logger.error("Failed to load bronze.%s: %s", TABLE_NAME, exc)
        sys.exit(1)
    finally:
        conn.close()
        logger.info("Connection closed")

    logger.info("Completed in %.2f seconds", time.time() - start_time)


if __name__ == "__main__":
    main()
