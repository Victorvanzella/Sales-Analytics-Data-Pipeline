select
    cast(customer_id as varchar) as customer_id,
    trim(cast(customer_name as varchar)) as customer_name,
    lower(trim(cast(email as varchar))) as email,
    trim(cast(segment as varchar)) as segment,
    trim(cast(city as varchar)) as city,
    upper(trim(cast(state as varchar))) as state,
    trim(cast(country as varchar)) as country,
    cast(signup_date as date) as signup_date,
    cast(updated_at as timestamp) as updated_at,
    cast(_ingested_at as timestamp) as _ingested_at
from {{ source('raw', 'customers') }}
