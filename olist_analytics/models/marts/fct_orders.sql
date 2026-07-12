select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    op.total_payment_value,
    op.payment_count,
    op.max_installments,
    op.payment_types,

    orv.review_score,
    orv.review_comment_title,
    orv.review_comment_message,
    orv.review_creation_date,
    orv.review_answer_timestamp,

    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state

from {{ ref('stg_olist__orders') }} o
inner join {{ ref('stg_olist__customers') }} c
    on o.customer_id = c.customer_id
left join {{ ref('int_orders_paid') }} op
    on o.order_id = op.order_id
left join {{ ref('int_orders_reviewed') }} orv
    on o.order_id = orv.order_id