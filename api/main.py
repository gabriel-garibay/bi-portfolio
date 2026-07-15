"""
FastAPI service exposing Olist CSV datasets as paginated JSON endpoints.
Mirrors TABLE_MAP structure so downstream extract_from_api() can consume
the same shape as extract_from_csv() did.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from shared.table_map import TABLE_MAP  # noqa: E402
import csv  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Load all tables into memory once, at startup.
_DATA: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    for table_name, config in TABLE_MAP.items():
        file_path = DATA_DIR / config["file"]
        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing {config['file']} in {DATA_DIR} — download the Olist dataset first"
            )
        with file_path.open("r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            _DATA[table_name] = [row for row in reader]
    yield
    _DATA.clear()


app = FastAPI(title="Olist Data API", version="1.0", lifespan=lifespan)


def _paginate(table_name: str, page: int, size: int) -> dict:
    if table_name not in _DATA:
        raise HTTPException(status_code=404, detail=f"Unknown table: {table_name}")

    records = _DATA[table_name]
    total = len(records)
    start = (page - 1) * size
    end = start + size

    return {
        "table": table_name,
        "page": page,
        "size": size,
        "total_rows": total,
        "total_pages": (total + size - 1) // size,
        "data": records[start:end],
    }


@app.get("/customers")
def get_customers(page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)):
    return _paginate("customers", page, size)


@app.get("/orders")
def get_orders(page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)):
    return _paginate("orders", page, size)


@app.get("/order_items")
def get_order_items(
    page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)
):
    return _paginate("order_items", page, size)


@app.get("/order_payments")
def get_order_payments(
    page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)
):
    return _paginate("order_payments", page, size)


@app.get("/order_reviews")
def get_order_reviews(
    page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)
):
    return _paginate("order_reviews", page, size)


@app.get("/products")
def get_products(page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)):
    return _paginate("products", page, size)


@app.get("/sellers")
def get_sellers(page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)):
    return _paginate("sellers", page, size)


@app.get("/geolocation")
def get_geolocation(
    page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)
):
    return _paginate("geolocation", page, size)


@app.get("/product_category_name_translation")
def get_category_translation(
    page: int = Query(1, ge=1), size: int = Query(1000, ge=1, le=10000)
):
    return _paginate("product_category_name_translation", page, size)
