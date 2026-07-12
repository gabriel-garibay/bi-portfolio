select
    order_id,
    order_item_id::int,
    product_id,
    seller_id,
    shipping_limit_date::timestamp,
    price::numeric,
    freight_value::numeric
from {{ source('bronze', 'order_items') }}