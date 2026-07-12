select
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    oi.shipping_limit_date,
    oi.price,
    oi.freight_value,
    erd.rate,
    oi.price * erd.rate as price_eur,
    oi.freight_value * erd.rate as freight_value_eur
from {{ ref('stg_olist__order_items') }} oi
inner join {{ ref('stg_olist__orders') }} o
    on oi.order_id = o.order_id
inner join {{ ref('int_exchange_rates_daily') }} erd
    on o.order_purchase_timestamp::date = erd.calendar_date