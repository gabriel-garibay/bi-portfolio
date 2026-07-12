select
    order_id,
    sum(payment_value) as total_payment_value,
    count(*) as payment_count,
    max(payment_installments) as max_installments,
    string_agg(distinct payment_type, ', ') as payment_types
from {{ ref('stg_olist__order_payments') }}
group by order_id