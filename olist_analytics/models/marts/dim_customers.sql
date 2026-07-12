select
    c.customer_id,
    c.customer_unique_id,
    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state,
    cg.avg_lat,
    cg.avg_lng,
    cg.city  as geo_city,
    cg.state as geo_state
from {{ ref('stg_olist__customers') }} c
left join {{ ref('int_geolocation_agg') }} cg
    on c.customer_zip_code_prefix = cg.zip_code_prefix