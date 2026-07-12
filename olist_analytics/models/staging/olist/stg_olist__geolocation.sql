select
    geolocation_zip_code_prefix,
    geolocation_lat::numeric,
    geolocation_lng::numeric,
    geolocation_city,
    geolocation_state
from {{ source('bronze', 'geolocation') }}