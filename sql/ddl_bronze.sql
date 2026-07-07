-- Raw mirror of the Olist source data.
-- PK strategy per table (informed by 01_explore.py findings):
    -- Tables with a natural unique key, with real business meaning, use that key directly.
        -- single: customers / orders / products / sellers / product_category_name_translation
        -- composite: order_items / order_payments / order_reviews / exchange_rates
    --  Geolocation has NO natural key and 26.18% exact duplicate rows -> uses a content hash (_row_hash)

CREATE SCHEMA IF NOT EXISTS bronze;

-- Source: olist_customers_dataset.csv
-- PK: customer_id (100% unique, 99441/99441 per exploration).
CREATE TABLE IF NOT EXISTS bronze.customers (
    customer_id TEXT,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (customer_id)
);

-- Source: olist_orders_dataset.csv
-- PK: order_id (100% unique, semantically better)
CREATE TABLE IF NOT EXISTS bronze.orders (
    order_id TEXT,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TEXT,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id)
);

-- Source: olist_order_items_dataset.csv
-- PK: (order_id, order_item_id)
CREATE TABLE IF NOT EXISTS bronze.order_items (
    order_id TEXT,
    order_item_id TEXT,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TEXT,
    price TEXT,
    freight_value TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, order_item_id)
);

-- Source: olist_order_payments_dataset.csv
-- PK: (order_id, payment_sequential)
CREATE TABLE IF NOT EXISTS bronze.order_payments (
    order_id TEXT,
    payment_sequential TEXT,
    payment_type TEXT,
    payment_installments TEXT,
    payment_value TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, payment_sequential)
);

-- Source: olist_order_reviews_dataset.csv
-- PK: (review_id, order_id) semantically better than ('order_id', 'review_answer_timestamp')
CREATE TABLE IF NOT EXISTS bronze.order_reviews (
    review_id TEXT,
    order_id TEXT,
    review_score TEXT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (review_id, order_id)
);

-- Source: olist_products_dataset.csv
-- PK: product_id
CREATE TABLE IF NOT EXISTS bronze.products (
    product_id TEXT,
    product_category_name TEXT,
    product_name_lenght TEXT,
    product_description_lenght TEXT,
    product_photos_qty TEXT,
    product_weight_g TEXT,
    product_length_cm TEXT,
    product_height_cm TEXT,
    product_width_cm TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (product_id)
);

-- Source: olist_sellers_dataset.csv
-- PK: seller_id
CREATE TABLE IF NOT EXISTS bronze.sellers (
    seller_id TEXT,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (seller_id)
);

-- Source: olist_geolocation_dataset.csv
-- No natural key - PK will be a content hash over all columns
CREATE TABLE IF NOT EXISTS bronze.geolocation (
    geolocation_zip_code_prefix TEXT,
    geolocation_lat TEXT,
    geolocation_lng TEXT,
    geolocation_city TEXT,
    geolocation_state TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    _row_hash TEXT,
    PRIMARY KEY (_row_hash)
);

-- Source: product_category_name_translation.csv
-- PK: product_category_name (based on column name)
CREATE TABLE IF NOT EXISTS bronze.product_category_name_translation (
    product_category_name TEXT,
    product_category_name_english TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (product_category_name)
);

-- Source: Frankfurter API (BRL/EUR) not part of the original Olist dataset (separate ingestion script)
-- It will serve to translate the data monetarily
CREATE TABLE IF NOT EXISTS bronze.exchange_rates (
    rate_date TEXT,
    base_currency TEXT,
    quote_currency TEXT,
    rate TEXT,
    _loaded_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (rate_date, base_currency, quote_currency)
);