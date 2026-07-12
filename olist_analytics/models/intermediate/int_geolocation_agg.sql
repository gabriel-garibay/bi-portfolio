select
    geolocation_zip_code_prefix as zip_code_prefix,
    avg(geolocation_lat) as avg_lat,
    avg(geolocation_lng) as avg_lng,
    min(geolocation_lat) as min_lat,
    max(geolocation_lat) as max_lat,
    min(geolocation_lng) as min_lng,
    max(geolocation_lng) as max_lng,
    count(*) as point_count,
    mode() within group (order by geolocation_city)  as city,
    mode() within group (order by geolocation_state) as state
from {{ ref('stg_olist__geolocation') }}
group by geolocation_zip_code_prefix