# Infrastructure setup step that runs once before the first pipeline execution, or after a database reset.

import logging
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# lee .env
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

DDL_FILES = [
    "ddl_bronze.sql",
]

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_ddl")


# Execute a single DDL file against the database
def run_ddl(conn, ddl_path: Path) -> None:
    if not ddl_path.exists():
        raise FileNotFoundError(f"DDL file not found: {ddl_path}")

    sql = ddl_path.read_text(encoding="utf-8")

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    logger.info("Executed: %s", ddl_path.name)


def main() -> None:
    logger.info("Starting DDL execution")

    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )
        logger.info("Connected to PostgreSQL")
    except psycopg2.OperationalError as exc:
        logger.error("Could not connect to PostgreSQL: %s", exc)
        raise

    try:
        for filename in DDL_FILES:
            run_ddl(conn, SQL_DIR / filename)
    finally:
        conn.close()
        logger.info("Connection closed")

    logger.info("DDL execution complete")


if __name__ == "__main__":
    main()
