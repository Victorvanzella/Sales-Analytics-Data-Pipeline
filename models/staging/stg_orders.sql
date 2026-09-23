select
    cast(order_id as varchar) as order_id,
    cast(customer_id as varchar) as customer_id,
    cast(order_date as date) as order_date,
    trim(cast(order_status as varchar)) as order_status,
    trim(cast(payment_method as varchar)) as payment_method,
    trim(cast(sales_channel as varchar)) as sales_channel,
    trim(cast(shipping_country as varchar)) as shipping_country,
    cast(updated_at as timestamp) as updated_at,
    cast(_ingested_at as timestamp) as _ingested_at
from {{ source('raw', 'orders') }}
