select
    md5(customer_id) as customer_sk,
    customer_id,
    customer_name,
    email,
    segment,
    city,
    state,
    country,
    signup_date,
    updated_at
from {{ ref('stg_customers') }}
