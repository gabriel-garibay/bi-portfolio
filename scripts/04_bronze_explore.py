import logging
import sys
from typing import List
from pg_load import get_connection
from psycopg2 import sql

logger = logging.getLogger("bronze_explore")

TABLES = [
    "customers",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "products",
    "sellers",
    "geolocation",
    "product_category_name_translation",
    "exchange_rates",
]

# Format: (child_table, child_column, parent_table, parent_column)
FK_CHECKS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("order_payments", "order_id", "orders", "order_id"),
    ("order_reviews", "order_id", "orders", "order_id"),
]

DATE_COLS_TO_CHECK = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
    ]
}

NUM_COLS_TO_CHECK = {
    "order_items": [
        "price",
        "freight_value",
        "order_item_id",
    ],
    "order_payments": [
        "payment_value",
        "payment_installments",
        "payment_sequential",
    ],
    "order_reviews": [
        "review_score",
    ],
    "products": [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "geolocation": [
        "geolocation_lat",
        "geolocation_lng",
    ],
}


# DATA QUALITY FUNCTIONS
def check_nulls_and_empties(conn, table: str) -> None:
    # Reports NULLs and empty strings per column in the Bronze layer
    with conn.cursor() as cur:
        # Fetch column names dynamically and securely
        cur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='bronze' AND table_name=%s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        cols = [r[0] for r in cur.fetchall() if not r[0].startswith("_")]

        if not cols:
            logger.warning(f"Table '{table}' has no columns or does not exist.")
            return

        # Build the dynamic SQL query securely
        checks = sql.SQL(", ").join(
            sql.SQL(
                "COUNT(*) FILTER (WHERE {c} IS NULL) AS {n1}, "
                "COUNT(*) FILTER (WHERE {c} = '') AS {n2}"
            ).format(
                c=sql.Identifier(c),
                n1=sql.Identifier(f"{c}_null"),
                n2=sql.Identifier(f"{c}_empty"),
            )
            for c in cols
        )

        # Execute a single table scan
        cur.execute(
            sql.SQL("SELECT COUNT(*), {} FROM bronze.{}").format(
                checks, sql.Identifier(table)
            )
        )
        row = cur.fetchone()

    # Parse and log results
    total_rows = row[0]
    logger.info(f"{table.upper()} ({total_rows:,} rows)")

    colnames = [d.name for d in cur.description][1:]
    counts = dict(zip(colnames, row[1:]))

    for c in cols:
        nulls, empties = counts[f"{c}_null"], counts[f"{c}_empty"]
        if nulls or empties:
            logger.info(f"{c}: {nulls:,} NULL, {empties:,} empty string")


def check_date_formats(conn, table: str, date_cols: List[str]) -> None:
    # Verifies that date columns match the YYYY-MM-DD pattern in a single scan
    regex_pattern = r"^\d{4}-\d{2}-\d{2}"

    with conn.cursor() as cur:
        checks = sql.SQL(", ").join(
            sql.SQL(
                "COUNT(*) FILTER (WHERE {c} IS NOT NULL AND {c} != '' AND {c} !~ %s) AS {bad_col}"
            ).format(c=sql.Identifier(col), bad_col=sql.Identifier(f"bad_{col}"))
            for col in date_cols
        )

        query = sql.SQL("SELECT {} FROM bronze.{}").format(
            checks, sql.Identifier(table)
        )

        cur.execute(query, (regex_pattern,) * len(date_cols))
        results = cur.fetchone()
        valid_cols = []
        for col, bad_count in zip(date_cols, results):
            if bad_count > 0:
                logger.warning(
                    f"FORMAT DRIFT: {table}.{col}: {bad_count} rows do not match YYYY-MM-DD"
                )
            else:
                valid_cols.append(col)
        if valid_cols:
            logger.info(f"Date format valid for all rows: {', '.join(valid_cols)}")


def check_numeric_formats(conn, table: str, numeric_cols: list[str]) -> None:
    # Verifies that TEXT columns intended to be numeric match a decimal or integer pattern.
    # Regex for standard numeric values (allows integers, decimals, and negative numbers)
    numeric_regex = r"^-?\d+(\.\d+)?$"

    with conn.cursor() as cur:
        checks = sql.SQL(", ").join(
            sql.SQL(
                "COUNT(*) FILTER (WHERE {c} IS NOT NULL AND {c} != '' AND {c} !~ %s) AS {bad_col}"
            ).format(c=sql.Identifier(col), bad_col=sql.Identifier(f"bad_{col}"))
            for col in numeric_cols
        )

        query = sql.SQL("SELECT {} FROM bronze.{}").format(
            checks, sql.Identifier(table)
        )

        cur.execute(query, (numeric_regex,) * len(numeric_cols))
        results = cur.fetchone()
        valid_cols = []
        for col, bad_count in zip(numeric_cols, results):
            if bad_count > 0:
                logger.warning(
                    f"NUMERIC FORMAT ERROR: {table}.{col} has {bad_count:,} rows that cannot be safely cast to NUMERIC."
                )
            else:
                valid_cols.append(col)
        if valid_cols:
            logger.info(f"Numeric format valid for all rows: {', '.join(valid_cols)}")


def check_fk_orphans(
    conn, child: str, child_col: str, parent: str, parent_col: str
) -> None:
    # Checks for orphaned records using an optimized NOT EXISTS anti-join
    query = sql.SQL("""
        SELECT COUNT(*) 
        FROM bronze.{child} c
        WHERE c.{child_col} IS NOT NULL 
          AND NOT EXISTS (
              SELECT 1 
              FROM bronze.{parent} p 
              WHERE p.{parent_col} = c.{child_col}
          )
    """).format(
        child=sql.Identifier(child),
        parent=sql.Identifier(parent),
        child_col=sql.Identifier(child_col),
        parent_col=sql.Identifier(parent_col),
    )

    with conn.cursor() as cur:
        cur.execute(query)
        orphans = cur.fetchone()[0]

    if orphans > 0:
        logger.warning(
            f"ORPHANS: {child}.{child_col} -> {parent}.{parent_col}: {orphans:,} orphans found"
        )
    else:
        logger.info(f"OK: {child}.{child_col} -> {parent}.{parent_col}: 0 orphans")


def check_exchange_rate_coverage(conn) -> None:
    # Confirms exchange_rates cover the entire order purchase date range
    with conn.cursor() as cur:
        cur.execute(
            "SELECT MIN(order_purchase_timestamp), MAX(order_purchase_timestamp) FROM bronze.orders"
        )
        o_min, o_max = cur.fetchone()

        cur.execute(
            "SELECT MIN(rate_date), MAX(rate_date), COUNT(*) FROM bronze.exchange_rates"
        )
        r_min, r_max, r_count = cur.fetchone()

    logger.info("--- EXCHANGE RATES COVERAGE ---")

    # Edge Case Handling: Empty tables or missing data
    if not o_min or not o_max:
        logger.warning("No valid purchase dates found in 'orders'.")
        return
    if not r_min or not r_max:
        logger.warning("No valid dates found in 'exchange_rates'.")
        return

    logger.info(f"Orders range: {o_min} -> {o_max}")
    logger.info(f"Rates range:  {r_min} -> {r_max} ({r_count:,} rows)")

    # Coverage validation (assuming the first 10 chars are YYYY-MM-DD)
    is_covered = (r_min[:10] <= o_min[:10]) and (r_max[:10] >= o_max[:10])

    if is_covered:
        logger.info("STATUS: Rates cover all orders.")
    else:
        logger.warning("STATUS: ALERT - Rates DO NOT cover all orders.")


def main() -> None:
    logger.info("Starting data quality analysis in BRONZE layer...")

    try:
        conn = get_connection()
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        sys.exit(1)

    try:
        for table in TABLES:
            check_nulls_and_empties(conn, table)

        logger.info("--- FK ORPHAN CHECKS ---")
        for args in FK_CHECKS:
            check_fk_orphans(conn, *args)

        logger.info("--- DATE FORMAT CHECKS ---")
        for table, cols in DATE_COLS_TO_CHECK.items():
            check_date_formats(conn, table, cols)

        logger.info("--- NUMERIC FORMAT CHECKS ---")
        for table, cols in NUM_COLS_TO_CHECK.items():
            check_numeric_formats(conn, table, cols)

        check_exchange_rate_coverage(conn)

    except Exception as e:
        logger.error(f"Fatal error during execution: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if "conn" in locals() and conn:
            conn.close()
            logger.info("Database connection closed.")


if __name__ == "__main__":
    main()
