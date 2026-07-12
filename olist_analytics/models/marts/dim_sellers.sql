select
    s.seller_id,
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    sg.avg_lat,
    sg.avg_lng,
    sg.city  as geo_city,
    sg.state as geo_state
from {{ ref('stg_olist__sellers') }} s
left join {{ ref('int_geolocation_agg') }} sg
    on s.seller_zip_code_prefix = sg.zip_code_prefix