{% snapshot customers_snapshot %}

{{
    config(
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at',
        invalidate_hard_deletes=True
    )
}}

select
    customer_id,
    customer_name,
    email,
    segment,
    city,
    state,
    country,
    signup_date,
    updated_at
from {{ source('raw', 'customers') }}

{% endsnapshot %}
