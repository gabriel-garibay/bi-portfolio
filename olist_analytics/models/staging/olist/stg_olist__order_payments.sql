select
    order_id,
    payment_sequential::int,
    payment_type,
    payment_installments::int,
    payment_value::numeric
from {{ source('bronze', 'order_payments') }}