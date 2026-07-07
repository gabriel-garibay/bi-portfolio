"""
Used by every loading script (bronze_load_olist.py, bronze_load_exchange.py, and any future one)
Connect (CSV, API, etc.), insert, and verify row counts against postgresql.
load_table() and verify_load() are fully source-agnostic. They only know about dicts, column names, and a table name.
"""

import logging
import os
from typing import Iterator

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pg_load")


def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        logger.info("Connected to PostgreSQL")
        return conn
    except psycopg2.OperationalError as exc:
        logger.error("Could not connect to PostgreSQL: %s", exc)
        raise


def load_table(
    conn,
    schema: str,
    table_name: str,
    columns: list[str],
    conflict_key: str,
    records: Iterator[dict],
) -> int:
    # Bulk-insert records into schema.table using execute_values. (Idempotent: ON CONFLICT DO NOTHING on conflict_key)
    rows = [tuple(record[col] for col in columns) for record in records]
    if not rows:
        logger.warning(
            "No rows extracted for %s.%s - skipping insert", schema, table_name
        )
        return 0
    col_list = ", ".join(columns)
    sql = f"""
        INSERT INTO {schema}.{table_name} ({col_list})
        VALUES %s
        ON CONFLICT {conflict_key} DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)
    conn.commit()

    return len(rows)


def verify_load(conn, schema: str, table_name: str) -> int:
    """Return row count for a table - used for the run summary."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
        return cur.fetchone()[0]
