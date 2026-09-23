with items as (
    select * from {{ ref('stg_order_items') }}
),

products as (
    select * from {{ ref('stg_products') }}
)

select
    items.order_item_id,
    items.order_id,
    items.product_id,
    products.product_name,
    products.category,
    products.subcategory,
    items.quantity,
    items.unit_price,
    products.unit_cost,
    items.discount_pct,
    round(items.quantity * items.unit_price, 2) as gross_sales_amount,
    round(items.quantity * items.unit_price * items.discount_pct, 2) as discount_amount,
    round(items.quantity * items.unit_price * (1 - items.discount_pct), 2) as net_sales_amount,
    round(items.quantity * products.unit_cost, 2) as cost_amount,
    round(
        items.quantity * items.unit_price * (1 - items.discount_pct)
        - items.quantity * products.unit_cost,
        2
    ) as margin_amount,
    items.source_item_total,
    items.updated_at,
    items._ingested_at
from items
inner join products on items.product_id = products.product_id
