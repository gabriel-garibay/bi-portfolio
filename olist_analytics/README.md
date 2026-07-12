# Olist Analytics — dbt Project

Analytics Engineering portfolio project: Medallion Architecture (Bronze → Silver → Gold) on the Olist Brazilian E-Commerce public dataset + Frankfurter API (BRL/EUR exchange rates).

## Stack
- dbt Core 1.12.0-rc2, dbt-postgres 1.10.2, dbt_utils 1.4.1
- PostgreSQL (database `de_portfolio`)
- Python 3.12 (bronze ingestion, outside this dbt project)

## Prerequisites
- PostgreSQL running locally with schemas `bronze`, `silver`, `gold` created.
- Bronze layer already populated (see `/reports/03_bronze_exploration_report.md` for ingestion details — bronze ingestion is a separate Python pipeline, not part of dbt).
- `.venv` with dependencies installed: .venv\Scripts\python.exe -m pip install dbt-postgres --break-system-packages

## Setup
1. cd olist_analytics
2. dbt deps -> installs dbt_utils
3. dbt debug -> validates connection
4. dbt run -> builds all models
5. dbt test -> runs all 45 tests

## Architecture
1. bronze (raw, Python ingestion)
2. staging/olist/* → schema silver, materialized as VIEW
3. intermediate/* → schema silver, materialized as TABLE
4. marts/* → schema gold, materialized as TABLE

Schema routing is defined in `dbt_project.yml`:
```yaml
models:
  olist_analytics:
    staging:
      +materialized: view
      +schema: silver
    intermediate:
      +materialized: table
      +schema: silver
    marts:
      +materialized: table
      +schema: gold
```

A custom macro (`macros/generate_schema_name.sql`) overrides dbt's default schema concatenation behavior, so `+schema: silver` resolves to exactly `silver` (not `<target_schema>_silver`).

## Models

### Staging (10 views, schema `silver`)
1:1 with bronze sources. No joins, no aggregation — only `NULLIF(col, '')` for empty strings, type casting, and typo correction.

| Model | Rows |
|---|---:|
| `stg_olist__customers` | 99,441 |
| `stg_olist__sellers` | 3,095 |
| `stg_olist__products` | 32,951 |
| `stg_olist__product_category_name_translation` | 71 |
| `stg_olist__geolocation` | 738,332 |
| `stg_olist__orders` | 99,441 |
| `stg_olist__order_items` | 112,650 |
| `stg_olist__order_payments` | 103,886 |
| `stg_olist__order_reviews` | 99,224 |
| `stg_olist__exchange_rates` | 547 |

### Intermediate (6 tables, schema `silver`)
Business logic and aggregations that don't yet belong in a mart.

| Model | Rows | Purpose |
|---|---:|---|
| `int_geolocation_agg` | 19,015 | Centroid (AVG lat/lng) + bounding box per zip_code_prefix |
| `int_products_translated` | 32,951 | Category translated to English, COALESCE fallback |
| `int_exchange_rates_daily` | 779 | Daily BRL→EUR rate, gaps filled via LOCF window function |
| `int_order_items_priced` | 112,650 | order_items + EUR conversion |
| `int_orders_paid` | 99,440 | Payments aggregated to 1 row/order |
| `int_orders_reviewed` | 98,673 | Most recent review per order (dedup via ROW_NUMBER) |

### Marts (5 tables, schema `gold`) — star schema
| Model | Type | Grain | Rows |
|---|---|---|---:|
| `fct_order_items` | Fact | 1 row per (order_id, order_item_id) | 112,650 |
| `fct_orders` | Fact | 1 row per order_id | 99,441 |
| `dim_products` | Dimension | 1 row per product_id | 32,951 |
| `dim_sellers` | Dimension | 1 row per seller_id | 3,095 |
| `dim_customers` | Dimension | 1 row per customer_id | 99,441 |

## Key Design Decisions

- **Two separate facts, not one:** `fct_orders` (order grain) holds payment totals and review scores; `fct_order_items` (item grain) does not — merging them would silently duplicate order-level values across multi-item orders.
- **Fan-out prevention:** `order_payments` (N rows/order) and `order_reviews` (up to 3 rows/order) are pre-aggregated in `intermediate/` before any join to a fact table.
- **LOCF via window function over LATERAL join:** `int_exchange_rates_daily` uses `MAX(rate_date) OVER (ORDER BY calendar_date)` for a single-pass fill of missing daily rates, favoring reusability/readability over the marginal performance edge of a per-row correlated subquery at this data volume (547 rates, 112,650 items).
- **Geolocation centroid, not raw points, in facts/dims:** `int_geolocation_agg` collapses 738,332 GPS points to 19,015 rows (1/zip) via arithmetic mean, to preserve join integrity (1:1) into sellers/customers. Raw granular data remains available as `stg_olist__geolocation` for independent density-map visuals in Power BI.
- **Denormalized attributes + separate dimensions coexist:** facts carry seller/customer/product attributes directly (fast ad-hoc SQL debugging) in addition to proper `dim_*` tables (Power BI semantic layer relationships). Trade-off accepted given the static nature of this dataset.

## Testing
45 dbt tests total (`unique`, `not_null`, `relationships`, `dbt_utils.unique_combination_of_columns` for composite PKs).
**41 PASS, 4 WARN (documented gaps, not errors), 0 ERROR.**

| Test | Count | Reason |
|---|---:|---|
| `fct_order_items.customer_lat` not_null | 302 | zip not present in geolocation dataset |
| `fct_order_items.seller_lat` not_null | 253 | zip not present in geolocation dataset |
| `fct_orders.review_score` not_null | 768 | order without a submitted review |
| `fct_orders.total_payment_value` not_null | 1 | order without a payment record |

## Documentation
Full lineage graph and column-level docs available via:
dbt docs generate
dbt docs serve

Layer-by-layer exploration reports (bronze/silver/gold) available in `/docs` at the repository root.

## Next Steps
1. Migrate CSV extraction to FastAPI (`extract_from_api()`).
2. Dockerize the pipeline.
3. Build Power BI semantic layer on `gold` schema (seller performance dashboard, time intelligence + DAX).