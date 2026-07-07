# Bronze Layer Exploration Report: OLIST Dataset
**Execution Date:** 2026-07-07
**Pipeline Status:** OK
**Target Database:** PostgreSQL (Layer: `bronze`)

---

## Dataset Volumetrics & Completeness

| Table Name | Total Rows | Columns with Missing Data (Empty Strings) | Status |
| :--- | :---: | :--- | :---: |
| `customers` | 99,441 | None | OK |
| `orders` | 99,441 | `order_approved_at` (160), `order_delivered_carrier_date` (1,783), `order_delivered_customer_date` (2,965) | Clean Needed |
| `order_items` | 112,650 | None | OK |
| `order_payments` | 103,886 | None | OK |
| `order_reviews` | 99,224 | `review_comment_title` (87,656), `review_comment_message` (58,247) | Expected |
| `products` | 32,951 | `product_category_name` (610), `product_weight_g` (2), `product_length_cm` (2), `product_height_cm` (2), `product_width_cm` (2) | Clean Needed |
| `sellers` | 3,095 | None | OK |
| `geolocation` | 738,332 | None | OK |
| `exchange_rates` | 547 | None | OK |

---

## Data Quality Alerts

### Date Format & Completeness Drift
* **`orders.order_approved_at`**: 160 rows are empty strings.
* **`orders.order_delivered_carrier_date`**: 1,783 rows are empty strings.
* **`orders.order_delivered_customer_date`**: 2,965 rows are empty strings.

### Numeric Format & Integrity
* **`products` table**: 2 rows have empty strings in dimensional fields (`product_weight_g`, `product_length_cm`, etc.).
* **Integrational Health**: All 16 numeric evaluation columns passed the regex validation check successfully.

---

## Relational & Dimension Coverage

### Foreign Key Checks
* `orders.customer_id` -> `customers.customer_id`: **0 orphans** -> OK
* `order_items.order_id` -> `orders.order_id`: **0 orphans** -> OK
* `order_items.product_id` -> `products.product_id`: **0 orphans** -> OK

### Exchange Rates Coverage
* **Orders Date Range:** `2016-09-04` to `2018-10-17`
* **Rates Date Range:** `2016-09-01` to `2018-10-19`
* **Coverage Status:** **100% Covered**. FX data safely encompasses all order transactions.

---

## Silver Layer Action Items (Backlog)

1. **Typo Correction:** Rename `product_name_lenght` to `product_name_length` and `product_description_lenght` to `product_description_length` in the `stg_products` model.
2. **Safe Casting:** Apply `NULLIF(column, '')` to all fields in `orders` and `products` that flagged empty strings before attempting `CAST(... AS TIMESTAMP)` or `CAST(... AS INT)`.
3. **Review Texts:** `review_comment_title` has an 88% missing data rate. Evaluate if this column provides statistical value or if it should be excluded from final analytical models.