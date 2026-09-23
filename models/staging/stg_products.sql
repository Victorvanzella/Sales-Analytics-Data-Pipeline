select
    cast(product_id as varchar) as product_id,
    trim(cast(product_name as varchar)) as product_name,
    trim(cast(category as varchar)) as category,
    trim(cast(subcategory as varchar)) as subcategory,
    cast(unit_cost as decimal(18, 2)) as unit_cost,
    cast(list_price as decimal(18, 2)) as list_price,
    cast(is_active as boolean) as is_active,
    cast(updated_at as timestamp) as updated_at,
    cast(_ingested_at as timestamp) as _ingested_at
from {{ source('raw', 'products') }}
