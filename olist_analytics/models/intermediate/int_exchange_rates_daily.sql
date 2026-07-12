with calendar as (
    select generate_series(
        (select min(rate_date) from {{ ref('stg_olist__exchange_rates') }}),
        (select max(rate_date) from {{ ref('stg_olist__exchange_rates') }}),
        interval '1 day'
    )::date as calendar_date
),

rates as (
    select rate_date, rate
    from {{ ref('stg_olist__exchange_rates') }}
    where base_currency = 'BRL'
      and quote_currency = 'EUR'
),

joined as (
    select
        c.calendar_date,
        r.rate,
        max(r.rate_date) over (
            order by c.calendar_date
        ) as last_known_date
    from calendar c
    left join rates r on c.calendar_date = r.rate_date
)

select
    j.calendar_date,
    r2.rate
from joined j
inner join rates r2 on j.last_known_date = r2.rate_date