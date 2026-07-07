# P01: E-Commerce Analytics Pipeline (Olist & FX)
### 🚀 Moving from BI Analyst to Analytics Engineer
A production-inspired, end-to-end data platform built to replicate modern Analytics Engineering workflows. This project models and transforms raw Brazilian e-commerce transaction data (Olist) and dynamic macroeconomic factors, implementing a robust **Medallion Architecture (Bronze -> Silver -> Gold)** in PostgreSQL using Python and **dbt Core**, finalizando con reportería avanzada en **Power BI**.

> **Data-Driven Engineering:** Every architecture decision—from composite PK selection to hash-based deduplication—is empirically verified through data exploration reports rather than structural assumptions.

---

## Data Architecture Workflow
* **[Raw Sources]** -> 9 Olist CSVs + Frankfurter API (BRL/EUR rates)
* **[Layer 1: Bronze]** -> PostgreSQL Target (Immutable Raw TEXT Mirror)
* **[Layer 2: Silver]** -> dbt Core Staging (Type Casting, Cleansing & Deduplication)
* **[Layer 3: Gold]** -> dbt Core Marts (Analytical Dimensions & Facts)
* **[BI Layer]** -> Power BI (Star Schema / Advanced DAX Time Intelligence)

---

## Tech Stack
* **Orchestration & Ingestion:** Python (`psycopg2`, `requests`, `FastAPI` *planned*)
* **Storage & Compute:** PostgreSQL 16+
* **Transformation & T-Modeling:** dbt Core (v1.8+)
* **Visualization & Analytics:** Power BI (Star Schema / Advanced DAX)
* **Version Control:** Git & GitHub

---

## Ingestion Pipeline Scripts (`/scripts`)

The ingestion layer is schema-agnostic, reusable, and designed with high modularity:

| Script | Purpose |
| :--- | :--- |
| `01_raw_explore.py` | **Pre-load profiling:** Evaluates PK candidates, duplicate thresholds, and null rates across 9 raw CSVs. |
| `02_bronze_ddl.py` | **Infrastructure Setup:** Executes DDL to build the strict `bronze` schema architecture. |
| `03_bronze_load_olist.py` | **Idempotent Ingestion:** Loads e-commerce datasets into Bronze using `ON CONFLICT` and synthetic hashing. |
| `03_bronze_load_exchange.py` | **API Integration:** Fetches `BRL/EUR` rates dynamically based on the transaction boundaries found in the data. |
| `04_bronze_explore.py` | **Post-load Quality Gate:** Validates row counts, detects foreign key orphans, and checks date conformities. |
| `pg_load.py` | **Core Utilities:** Reusable, database-agnostic connection and bulk-insert manager. |

---

## Key Design Decisions & Quality Gates

### 1. The Bronze ELT Philosophy
The Bronze layer acts as an **immutable, raw text mirror** of the source system. No schema casting, cleansing, or trimming happens in Python. This guarantees full auditability. All type safety, structural casting, and business re-modeling are deferred entirely to **dbt**.

### 2. Empirical Key Verification (No Assumptions)
* **Composite Keys:** While `review_id` sounds like a natural Primary Key, profiling revealed it repeats **814 times** across distinct reviews. The true operational grain is composite: `(review_id, order_id)`.
* **Synthetic PKs via Hashing:** The `geolocation` dataset contains **26.18% exact duplicate rows** and lacks a natural key. Instead of dropping data blindly, an MD5 content hash (`_row_hash`) was engineered across all business attributes to act as a deterministic, synthetic PK.

### 3. Idempotency by Design
Every Python script and SQL load operation is completely idempotent. By using `ON CONFLICT DO NOTHING` statements, the pipelines can be executed repeatedly at any frequency without risking data duplication or pipeline crashes.

### 4. Dynamic Financial Integration (Macro Factors)
To evaluate metrics in Euros, the pipeline queries the Frankfurter API. The requested date range is **computed dynamically** via SQL from `bronze.orders` (from `2016-09-01` to `2018-10-20`). 
* *Why?* Choosing the order purchase timestamp over the payment approval timestamp was critical: business prices are locked at checkout, and **30.9% of orders** present a multi-day lag before final payment approval.

---

## Project Evolution Roadmap

To showcase senior-level data architecture scaling, this project is transitioning across three implementation phases:

* [x] **Phase 1: Local Ingestion Architecture (Completed)** -> Python raw ingestion + API boundary calls + PostgreSQL.
* [ ] **Phase 2: Modern Ingestion & Medallion (In Progress)** -> Encapsulate CSV sources into a high-performance **FastAPI microservice** to simulate streaming/application ingestion. Migrate transformation workflows to full **dbt Core staging and marts models**.
* [ ] **Phase 3: Semantic BI Layer** -> Build an analytical Star Schema in **Power BI**, implementing advanced time-intelligence DAX measures to analyze sales, logistics performance, and currency conversion impact.