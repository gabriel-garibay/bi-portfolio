# Gold Layer Exploration Report: OLIST Dataset
**Execution Date:** 2026-07-12
**Pipeline Status:** OK
**Target Database:** PostgreSQL (Layer: `gold`)
**Tooling:** dbt Core 1.12.0-rc2, dbt-postgres 1.10.2

---

## Star Schema Overview

| Model | Type | Grain | Rows | Status |
| :--- | :---: | :--- | :---: | :---: |
| `fct_order_items` | Fact | 1 row per (order_id, order_item_id) | 112,650 | OK |
| `fct_orders` | Fact | 1 row per order_id | 99,441 | OK |
| `dim_products` | Dimension | 1 row per product_id | 32,951 | OK |
| `dim_sellers` | Dimension | 1 row per seller_id | 3,095 | OK |
| `dim_customers` | Dimension | 1 row per customer_id | 99,441 | OK |

All fact row counts match exact parity with their source staging tables — no fan-out duplication from joins.

---

## Fact Table Design

### `fct_order_items`
Joins: `int_order_items_priced` (inner) + `stg_olist__orders` (inner) + `int_products_translated` (inner) + `stg_olist__sellers` (inner) + `stg_olist__customers` (inner) + `int_geolocation_agg` ×2 (left, seller/customer).

Excludes `review_score` and `total_payment_value` — both are 1:N with items within multi-item orders; including them here would silently inflate any SUM/AVG performed at item grain.

### `fct_orders`
Joins: `stg_olist__orders` (inner) + `stg_olist__customers` (inner) + `int_orders_paid` (left) + `int_orders_reviewed` (left).

---

## Data Quality Alerts

### Geolocation Coverage Gaps
* `fct_order_items.customer_lat`: 302 NULLs (0.27%) — customer zip absent from geolocation dataset.
* `fct_order_items.seller_lat`: 253 NULLs (0.22%) — seller zip absent from geolocation dataset.
* Assessment: marginal, non-blocking for map visualization use case.

### Order-Level Coverage Gaps
* `fct_orders.review_score`: 768 NULLs (0.77%) — orders without a submitted review (expected).
* `fct_orders.total_payment_value`: 1 NULL (0.001%) — order without a payment record.

All gaps configured as `severity: warn` (not `error`) — documented, not blocking.

---

## Testing

18 additional tests on marts. **Full project: 45 tests, 41 PASS, 4 WARN, 0 ERROR.**

---

## Design Decisions

1. **Two facts, not one:** item-grain and order-grain kept separate to prevent fan-out inflation of order-level metrics (payment, review) across multi-item orders.
2. **Denormalization + dimensions coexist:** facts carry seller/customer/product attributes directly (fast ad-hoc SQL) *and* separate `dim_*` tables exist for Power BI's semantic layer (proper star schema relationships, slicers, hierarchies). Trade-off accepted: storage duplication, low consistency risk on this static dataset.
3. **Geolocation centroid, not raw points, used in facts/dims:** raw 738K-point `stg_olist__geolocation` remains available as an independent Power BI table for density-style visualizations, without an active relationship to the fact tables.

---

## Next Steps (Backlog)

1. Migrate CSV extraction to FastAPI (`extract_from_api()` replacing `extract_from_csv()`).
2. Dockerize the full pipeline.
3. Build Power BI semantic layer on `gold` schema; seller performance dashboard with time intelligence and RANKX DAX measures.