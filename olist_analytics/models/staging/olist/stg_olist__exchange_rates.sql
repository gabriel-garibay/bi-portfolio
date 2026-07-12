select
    rate_date::date,
    base_currency,
    quote_currency,
    rate::numeric
from {{ source('bronze', 'exchange_rates') }}