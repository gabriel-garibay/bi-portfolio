-- BD: de-portfolio
-- Tables: dim_date, dim_customer, dim_seller, dim_product,fact_order_items, fact_payments, fact_reviews, geolocation

-- dim_date (will cover 2016-01-01 to 2018-12-31)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id DATE PRIMARY KEY,
    year_number SMALLINT NOT NULL,
    quarter_number SMALLINT NOT NULL,
    month_number SMALLINT NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    week_number SMALLINT NOT NULL,
    day_number SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    day_name VARCHAR(10) NOT NULL
);
-- dim_customer
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL, -- identifies the real-world customer across orders (for analysis)
    zip_code_prefix CHAR(5) NOT NULL, -- Normalized during the cleaning process (postal code)
    customer_city VARCHAR(50) NOT NULL,
    customer_state CHAR(2) NOT NULL
);
-- geolocation
CREATE TABLE IF NOT EXISTS geolocation (
    zip_code_prefix CHAR(5) NOT NULL, -- multiple coordinate records exist per ZIP code (no PK)
    lat NUMERIC(9,6) NOT NULL,
    lng NUMERIC(9,6) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state CHAR(2) NOT NULL
);
-- dim_order
CREATE TABLE IF NOT EXISTS dim_order (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    order_purchase_date DATE NOT NULL, -- FK to dim_date
    order_purchase_timestamp TIMESTAMP NOT NULL, -- preserves full precision
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date DATE, -- no value hh:mm:ss
    -- Key constraints
    FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    FOREIGN KEY (order_purchase_date) REFERENCES dim_date(date_id)
);
-- dim_product
CREATE TABLE IF NOT EXISTS dim_product (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100), -- in English (joined from translation table at load)
    product_name_length SMALLINT, -- Typo in source CSV corrected: lenght -> length.
    product_description_length SMALLINT,
    product_photos_qty SMALLINT,
    product_weight_g NUMERIC(10,2),
    product_length_cm NUMERIC(10,2),
    product_height_cm NUMERIC(10,2),
    product_width_cm NUMERIC(10,2)
);
-- dim_seller
CREATE TABLE IF NOT EXISTS dim_seller (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix CHAR(5) NOT NULL,
    seller_city VARCHAR(100) NOT NULL,
    seller_state CHAR(2) NOT NULL
);
-- fact_order_items
CREATE TABLE IF NOT EXISTS fact_order_items (
    order_id VARCHAR(50) NOT NULL,
    order_item_id SMALLINT NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,
    shipping_limit_date TIMESTAMP,
    price NUMERIC(10,2) NOT NULL,
    freight_value NUMERIC(10,2) NOT NULL,
    -- Key constraints
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES dim_order(order_id),
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
    FOREIGN KEY (seller_id) REFERENCES dim_seller(seller_id)
);
-- fact_payments
CREATE TABLE IF NOT EXISTS fact_payments (
    order_id VARCHAR(50) NOT NULL,
    payment_sequential SMALLINT NOT NULL,
    payment_type VARCHAR(20) NOT NULL,
    payment_installments SMALLINT NOT NULL,
    payment_value NUMERIC(10,2) NOT NULL,
    -- Key constraints
    PRIMARY KEY (order_id, payment_sequential), -- Grain: one row per payment method per order
    FOREIGN KEY (order_id) REFERENCES dim_order(order_id)
);
-- fact_reviews
CREATE TABLE IF NOT EXISTS fact_reviews (
    review_id VARCHAR(50) PRIMARY KEY, -- Multiple reviews per order confirmed
    order_id VARCHAR(50) NOT NULL,
    review_score SMALLINT NOT NULL,
    review_comment_title VARCHAR(100),
    review_comment_message TEXT, -- no limit
    review_creation_date DATE, -- no value hh:mm:ss
    review_answer_timestamp TIMESTAMP,
    -- Key constraints
    FOREIGN KEY (order_id)  REFERENCES dim_order(order_id)
);