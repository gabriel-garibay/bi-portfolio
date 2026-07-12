# Silver Layer Exploration Report: OLIST Dataset
**Execution Date:** 2026-07-10
**Pipeline Status:** OK
**Target Database:** PostgreSQL (Layer: `silver`)
**Tooling:** dbt Core 1.12.0-rc2, dbt-postgres 1.10.2

---

## Staging Models (10 views)

| Model | Source Rows | Empty Strings Handled | Status |
| :--- | :---: | :--- | :---: |
| `stg_olist__customers` | 99,441 | None | OK |
| `stg_olist__sellers` | 3,095 | None | OK |
| `stg_olist__products` | 32,951 | `product_category_name` (610), weight/dims (2 each) | Cleaned |
| `stg_olist__product_category_name_translation` | 71 | None | OK |
| `stg_olist__geolocation` | 738,332 | None | OK |
| `stg_olist__orders` | 99,441 | `order_approved_at` (160), `order_delivered_carrier_date` (1,783), `order_delivered_customer_date` (2,965) | Cleaned |
| `stg_olist__order_items` | 112,650 | None | OK |
| `stg_olist__order_payments` | 103,886 | None | OK |
| `stg_olist__order_reviews` | 99,224 | `review_comment_title` (87,656), `review_comment_message` (58,247) | Cleaned |
| `stg_olist__exchange_rates` | 547 | None | OK |

Transformations applied per bronze backlog: `NULLIF(col, '')` before casting, typo fix (`lenght` → `length`), type casts to TIMESTAMP/NUMERIC/INT.

---

## Intermediate Models (6 tables)

| Model | Output Rows | Logic | Status |
| :--- | :---: | :--- | :---: |
| `int_geolocation_agg` | 19,015 | Centroid (AVG lat/lng) + bounding box + point_count, grouped by `zip_code_prefix` | OK |
| `int_products_translated` | 32,951 | LEFT JOIN category translation, COALESCE fallback to original name | OK |
| `int_exchange_rates_daily` | 779 | 547 daily rates expanded to full calendar range via LOCF (window function) | OK |
| `int_order_items_priced` | 112,650 | order_items + BRL→EUR conversion via daily rate join | OK |
| `int_orders_paid` | 99,440 | Payments aggregated 1 row/order (SUM, COUNT, MAX installments) | Gap: 1 order unpaid |
| `int_orders_reviewed` | 98,673 | Reviews deduplicated 1 row/order (most recent by `review_answer_timestamp`) | Gap: 768 orders unreviewed |

---

## Data Quality Alerts

### Geolocation Aggregation
* Raw dataset: 738,332 GPS points → collapsed to 19,015 unique zip codes.
* Method: arithmetic mean (centroid), chosen over mode for map-visualization standard practice.

### Exchange Rate Gap-Filling
* Source: 547 daily BRL/EUR rates (Frankfurter API), non-contiguous (weekends/holidays missing).
* Method: LOCF via `MAX(rate_date) OVER (ORDER BY calendar_date)`, single-pass window function — chosen over per-row `LATERAL JOIN` for maintainability and reusability at this data volume (547 rates, 112,650 items).
* Confirmed direction: `rate` = EUR per 1 BRL (range ~0.15–0.28).

### Multi-Row Aggregation Risk (Fan-Out Prevention)
* `order_reviews`: up to 3 reviews per `order_id` detected. Deduplicated via `ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC)` before any downstream join, to prevent row duplication in gold.
* `order_payments`: N rows per `order_id` (installments). Pre-aggregated via SUM/COUNT before any downstream join, same reason.

---

## Testing

27 tests on staging models (`unique`, `not_null`, `relationships`, `dbt_utils.unique_combination_of_columns` for composite PKs). **27/27 PASS.**

---

## Gold Layer Action Items (Backlog)

1. **Fact Grain Separation:** `fct_order_items` (item grain) and `fct_orders` (order grain) must remain separate — merging payment/review data into item grain would duplicate values across multi-item orders.
2. **Denormalization Trade-off:** decide whether facts carry denormalized seller/customer/product attributes alongside separate dimension tables (chosen: yes, intentional duplication).
3. **Known Gaps to Propagate as WARN (not ERROR):** 302 customer / 253 seller zip codes absent from geolocation dataset; 768 orders without review; 1 order without payment.