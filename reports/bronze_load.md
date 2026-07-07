# Bronze Layer Ingestion Report
**Execution Date:** 2026-07-06
**Pipeline Status:** OK
**Target Database:** PostgreSQL (Layer: `bronze`)

---

## Ingestion Volumetrics Summary

| Target Table | Source File / API | Attempted | New Rows | Skipped (Duplicates) | Total Rows in Bronze | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `customers` | `olist_customers_dataset.csv` | 99,441 | 99,441 | 0 | 99,441 | OK |
| `orders` | `olist_orders_dataset.csv` | 99,441 | 99,441 | 0 | 99,441 | OK |
| `order_items` | `olist_order_items_dataset.csv` | 112,650 | 112,650 | 0 | 112,650 | OK |
| `order_payments` | `olist_order_payments_dataset.csv` | 103,886 | 103,886 | 0 | 103,886 | OK |
| `order_reviews` | `olist_order_reviews_dataset.csv` | 99,224 | 99,224 | 0 | 99,224 | OK |
| `products` | `olist_products_dataset.csv` | 32,951 | 32,951 | 0 | 32,951 | OK |
| `sellers` | `olist_sellers_dataset.csv` | 3,095 | 3,095 | 0 | 3,095 | OK |
| `geolocation` | `olist_geolocation_dataset.csv` | 1,000,163 | 738,332 | 261,831 | 738,332 | Deduplicated |
| `product_category_name_translation` | `product_category_name_translation.csv` | 71 | 71 | 0 | 71 | OK |
| `exchange_rates` | `Frankfurter API` (BRL/EUR) | 547 | 547 | 0 | 547 | OK |

---

## Performance & Execution Windows
The ingestion process ran across two operational windows to fetch core business transactional data and financial metrics dynamically.

### Window 1: Olist E-Commerce Datasets
* **Start Time:** 2026-07-06 13:40:05
* **End Time:** 2026-07-06 13:40:48
* **Total Duration:** 43.14 seconds

### Window 2: Currency Exchange Rates Ingestion
* **Start Time:** 2026-07-06 14:08:44
* **End Time:** 2026-07-06 14:08:45
* **Total Duration:** 0.84 seconds
* **Parameters Evaluated:** Currency pair `BRL/EUR` ranging from `2016-09-01` to `2018-10-20` (dynamically computed from orders history).

---

## Engineering Notes & Observations

### Idempotency & Conflict Handling
* **`geolocation` Deduplication:** The ingestion script successfully isolated **261,831 duplicates** using the `ON CONFLICT` strategy. The source file contained a significant amount of identical coordinates which were safely skipped to ensure the grain of the table remains clean.
* All other tables exhibited a 100% match between attempted records and new rows inserted, confirming no primary key clashes occurred during this load execution.

### Next Steps
1. Hand off control to `04_bronze_explore.py` to check post-load formatting and relational completeness tests.
2. Once quality validations pass, data is cleared to begin the transformation workflow toward the Silver schema.