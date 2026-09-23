select
    md5(product_id) as product_sk,
    product_id,
    product_name,
    category,
    subcategory,
    unit_cost,
    list_price,
    is_active,
    updated_at
from {{ ref('stg_products') }}
