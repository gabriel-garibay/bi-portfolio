select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp::timestamp,
    nullif(order_approved_at, '')::timestamp as order_approved_at,
    nullif(order_delivered_carrier_date, '')::timestamp as order_delivered_carrier_date,
    nullif(order_delivered_customer_date, '')::timestamp as order_delivered_customer_date,
    order_estimated_delivery_date::timestamp
from {{ source('bronze', 'orders') }}