# Raw Datasets Profiling & Exploration Report
**Execution Date:** 2026-07-01 
**Objective:** Primary Key empirical identification, Null-rate diagnostics, and Volumetric Profiling across 9 raw files.

---

## Dataset Granularity & Integrity Overview

| Target Entity | Total Rows | Total Cols | Identified PK Type | Selected PK Candidate / Strategy | Missing Records (Nulls) | Duplicate Rows % |
| :--- | :---: | :---: | :--- | :--- | :--- | :---: |
| `CUSTOMERS` | 99,441 | 5 | Simple | `customer_id` | None | 0.00% |
| `ORDERS` | 99,441 | 8 | Simple | `order_id` *(See Notes)* | Found in Lifecycle Dates | 0.00% |
| `ORDER_ITEMS` | 112,650 | 7 | Composite | `(order_id, order_item_id)` | None | 0.00% |
| `ORDER_PAYMENTS` | 103,886 | 5 | Composite | `(order_id, payment_sequential)` | None | 0.00% |
| `ORDER_REVIEWS` | 99,224 | 7 | Composite | `(review_id, order_id)` | Critical in text logs | 0.00% |
| `PRODUCTS` | 32,951 | 9 | Simple | `product_id` | 1.85% (Category, Specs) | 0.00% |
| `SELLERS` | 3,095 | 4 | Simple | `seller_id` | None | 0.00% |
| `GEOLOCATION` | 1,000,163 | 5 | No Natural Key | Content MD5 Hash (`_row_hash`) | None | 26.18% |
| `TRANSLATIONS` | 71 | 2 | Simple / Unique | `product_category_name` | None | 0.00% |

---

## Deep-Dive Technical Findings per Dataset

### CUSTOMERS
* **Data Typings:** Text structural data, except for `customer_zip_code_prefix` (`int64`).
* **Granularity Check:** `customer_id` matches the exact row count (99,441 unique values), making it the absolute identifier for transactional joins.

### ORDERS
* **The Lifecycle Drift:** Core null values are concentrated across workflow milestones:
  * `order_approved_at`: 160 missing rows (0.16%)
  * `order_delivered_carrier_date`: 1,783 missing rows (1.79%)
  * `order_delivered_customer_date`: 2,965 missing rows (2.98%)
* > **Modeling Warning:** Although `['order_id', 'customer_id']` both yield 100% mathematical uniqueness individually, `order_id` must be selected as the functional Primary Key to adhere to transactional relational architecture rules.

### ORDER_ITEMS
* **Granularity Analysis:** `order_id` drops to 98,666 unique occurrences over 112,650 total rows. 
* **Design Decision:** `order_item_id` serves as a sequential counter per order (Max value: 21). Uniqueness is strictly satisfied under the composite layout: `[(order_id, order_item_id)]`.

### ORDER_PAYMENTS
* **Granularity Analysis:** Multiple payment structures applied to a single transaction instance.
* **Design Decision:** Requires a composite constraint composed of `[(order_id, payment_sequential)]` to safely encapsulate splitting patterns (e.g., credit card voucher combinations).

### ORDER_REVIEWS
* **Text Heavy Null Footprint:** Extreme structural drift identified in text fields:
  * `review_comment_title`: 87,656 null records (**88.34% missing rate**)
  * `review_comment_message`: 58,247 null records (**58.70% missing rate**)
* > **Key Verification:** Testing single candidate keys showed `review_id` alone is NOT unique (98,410 unique values over 99,224 rows). Uniqueness is achieved empirically via `(review_id, order_id)`.

### PRODUCTS
* **Dimensional Drift:** 610 records (1.85% of rows) are missing `product_category_name`, descriptions, names lengths, and photo counts concurrently. 
* **Logistical Edge Cases:** 2 rows are missing physical dimensions (`product_weight_g`, etc.).
* **Typo Alert:** Columns `product_name_lenght` and `product_description_lenght` contain spelling errors directly in the raw data source.

### GEOLOCATION
* **Massive Structural Duplication:** The file contains **261,831 exact row replicas (26.18%)**.
* **Architecture Strategy:** No combination of business keys ensures constraint enforcement. It requires a synthetic, deterministic content-hash fingerprint (`_row_hash`) processed via `MD5` over all columns during raw preprocessing.

---

## Concrete Directive for `02_bronze_ddl.py`
Initialize all incoming dates (`order_approved_at`, `review_answer_timestamp`, etc.) and optional numeric specifications as `TEXT` data types inside the Bronze layer. This guarantees safe raw mirror ingestion without structural termination risks.