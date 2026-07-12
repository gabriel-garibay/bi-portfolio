select
    oip.order_id,
    oip.order_item_id,
    o.customer_id,
    oip.seller_id,
    oip.product_id,

    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    oip.shipping_limit_date,
    oip.price,
    oip.freight_value,
    oip.rate,
    oip.price_eur,
    oip.freight_value_eur,

    pt.product_category_name,
    pt.product_category_name_english,
    pt.product_weight_g,

    s.seller_zip_code_prefix,
    sg.avg_lat as seller_lat,
    sg.avg_lng as seller_lng,
    sg.city as seller_city,
    sg.state as seller_state,

    c.customer_zip_code_prefix,
    cg.avg_lat as customer_lat,
    cg.avg_lng as customer_lng,
    cg.city as customer_city,
    cg.state as customer_state

from {{ ref('int_order_items_priced') }} oip
inner join {{ ref('stg_olist__orders') }} o
    on oip.order_id = o.order_id
inner join {{ ref('int_products_translated') }} pt
    on oip.product_id = pt.product_id
inner join {{ ref('stg_olist__sellers') }} s
    on oip.seller_id = s.seller_id
inner join {{ ref('stg_olist__customers') }} c
    on o.customer_id = c.customer_id
left join {{ ref('int_geolocation_agg') }} sg
    on s.seller_zip_code_prefix = sg.zip_code_prefix
left join {{ ref('int_geolocation_agg') }} cg
    on c.customer_zip_code_prefix = cg.zip_code_prefix