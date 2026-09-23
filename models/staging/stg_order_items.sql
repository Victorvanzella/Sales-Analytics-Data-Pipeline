select
    cast(order_item_id as varchar) as order_item_id,
    cast(order_id as varchar) as order_id,
    cast(product_id as varchar) as product_id,
    cast(quantity as integer) as quantity,
    cast(unit_price as decimal(18, 2)) as unit_price,
    cast(discount_pct as decimal(8, 4)) as discount_pct,
    cast(item_total as decimal(18, 2)) as source_item_total,
    cast(updated_at as timestamp) as updated_at,
    cast(_ingested_at as timestamp) as _ingested_at
from {{ source('raw', 'order_items') }}
