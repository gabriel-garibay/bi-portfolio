# P01: E-Commerce Analytics Pipeline (Olist & FX)
### 🚀 Moving from BI Analyst to Analytics Engineer
A production-inspired, end-to-end data platform built to replicate modern Analytics Engineering workflows. This project models and transforms raw Brazilian e-commerce transaction data (Olist) and dynamic macroeconomic factors, implementing a robust **Medallion Architecture (Bronze -> Silver -> Gold)** in PostgreSQL using Python, **FastAPI**, and **dbt Core**, concluding with advanced reporting in **Power BI**.

> **Data-Driven Engineering:** Every architecture decision—from composite PK selection to hash-based deduplication to fact-grain separation—is empirically verified through data exploration reports rather than structural assumptions. Full rationale for each layer lives in [`/reports`](./reports).

---

## Project Evolution Roadmap

* [x] **Phase 1: Local Ingestion Architecture** — Python raw ingestion + API boundary calls + PostgreSQL.
* [x] **Phase 2: Modern Ingestion & Medallion** — FastAPI microservice replacing CSV extraction; full dbt Core staging, intermediate, and marts models (star schema in `gold`).
* [ ] **Phase 3: Semantic BI Layer** — Power BI Star Schema with advanced DAX time-intelligence measures for sales, logistics, and currency-conversion analysis.

---

## Data Architecture Workflow
* **[Raw Sources]** → 9 Olist CSVs (served via FastAPI) + Frankfurter API (BRL/EUR rates)
* **[Layer 1: Bronze]** → PostgreSQL Target (Immutable Raw TEXT Mirror)
* **[Layer 2: Silver]** → dbt Core Staging + Intermediate (Type Casting, Cleansing, Deduplication, Business Logic)
* **[Layer 3: Gold]** → dbt Core Marts (Star Schema: Facts & Dimensions)
* **[BI Layer]** → Power BI (Star Schema / Advanced DAX Time Intelligence) — *in progress*

---

## Tech Stack
* **Orchestration & Ingestion:** Python (`psycopg2`, `requests`), **FastAPI**
* **Transformation & Modeling:** dbt Core 1.12, `dbt_utils`
* **Storage & Compute:** PostgreSQL 16+
* **Visualization & Analytics:** Power BI (Star Schema / Advanced DAX) — *upcoming*
* **Version Control:** Git & GitHub

---

## Project Structure & Documentation

| Component | Details |
| :--- | :--- |
| `/scripts` | Python ingestion pipeline — see table below |
| `/api` | FastAPI service exposing source data as paginated endpoints |
| `/olist_analytics` | dbt Core project (silver + gold layers) — see its [README](./olist_analytics/README.md) for model-level detail |
| `/reports` | Sequential exploration & design-decision reports per layer (see below) |

### Ingestion Pipeline Scripts (`/scripts`)

| Script | Purpose |
| :--- | :--- |
| `01_raw_explore.py` | Pre-load profiling: PK candidates, duplicate thresholds, null rates across 9 raw CSVs |
| `02_bronze_ddl.py` | Infrastructure setup: builds the `bronze` schema |
| `03_bronze_load_olist.py` | Idempotent ingestion via FastAPI or CSV (`extract_from_api()` / `extract_from_csv()`) |
| `03_bronze_load_exchange.py` | Fetches BRL/EUR rates dynamically from Frankfurter API |
| `04_bronze_explore.py` | Post-load quality gate: row counts, FK orphans, date conformity |
| `pg_load.py` | Reusable connection and bulk-insert utilities |

*(`ml_category_diagnostic.py` also lives in `/scripts` but is exploratory — see [Key Design Decisions §7](#7-ml-based-category-imputation-tested-not-adopted).)*

**Full technical detail — data quality findings, design trade-offs, and test results — lives in the reports below, not in this file:**

| Report | Covers |
| :--- | :--- |
| [`01_raw_exploration.md`](./reports/01_raw_exploration.md) | PK candidate profiling, duplicate/null analysis on raw CSVs |
| [`02_bronze_load.md`](./reports/02_bronze_load.md) | Bronze ingestion design |
| [`03_bronze_exploration.md`](./reports/03_bronze_exploration.md) | Post-load quality gate: FK orphans, date/numeric conformity, FX coverage |
| [`04_silver_exploration.md`](./reports/04_silver_exploration.md) | Staging + intermediate models, LOCF FX gap-filling, fan-out prevention |
| [`05_gold_exploration.md`](./reports/05_gold_exploration.md) | Star schema design, fact grain separation, test coverage |
| [`06_fastapi_migration.md`](./reports/06_fastapi_migration.md) | CSV → FastAPI extraction migration, interface-contract validation |
| [`ml_category_diagnostic.md`](./reports/exploratory/ml_category_diagnostic.md) | RandomForest diagnostic on physical dimensions as `product_category_name` predictor — not adopted in production |

---

## Key Design Decisions

### 1. The Bronze ELT Philosophy
The Bronze layer acts as an **immutable, raw text mirror** of the source system. No schema casting, cleansing, or trimming happens in Python — all type safety and business re-modeling are deferred entirely to **dbt**.

### 2. Empirical Key Verification (No Assumptions)
* **Composite Keys:** `review_id` repeats **814 times** across distinct reviews — true grain is `(review_id, order_id)`.
* **Synthetic PKs via Hashing:** `geolocation` has **26.18% exact duplicate rows** and no natural key; an MD5 content hash (`_row_hash`) serves as a deterministic synthetic PK.

### 3. Idempotency by Design
Every script and SQL load is idempotent via `ON CONFLICT DO NOTHING` — safe to re-run at any frequency.

### 4. Interface-Contract Extraction Layer
`extract_from_csv()` and `extract_from_api()` share an identical `Iterator[dict]` output contract. Swapping the ingestion source (local CSV → FastAPI service) required a single-line change in the pipeline's orchestration — validated with exact row-count parity across all 9 tables. Details in [`06_fastapi_migration.md`](./reports/06_fastapi_migration.md).

### 5. Dynamic FX Date-Range Integration
The Frankfurter API request range is computed dynamically from `bronze.orders` (`2016-09-01` → `2018-10-20`), rather than hardcoded. `order_purchase_timestamp` was chosen over `order_approved_at` as the anchor: **30.9% of orders** show a multi-day lag between purchase and payment approval, and business prices are locked at checkout, not at approval.

### 6. Fan-Out Prevention in Gold
`order_payments` and `order_reviews` are pre-aggregated in the intermediate layer before any join to a fact table, preventing silent row duplication across multi-item orders. Two separate facts (`fct_order_items`, `fct_orders`) are kept at different grains rather than merged. Full rationale in [`05_gold_exploration.md`](./reports/05_gold_exploration.md).

### 7. ML-Based Category Imputation: Tested, Not Adopted
A RandomForest diagnostic tested whether physical product dimensions predict missing `product_category_name`. Result: 33.7% accuracy across 71 categories — well above baseline, but too low to trust over an explicit `NULL`. Full method and results in [`ml_category_diagnostic.md`](./reports/ml_category_diagnostic.md).