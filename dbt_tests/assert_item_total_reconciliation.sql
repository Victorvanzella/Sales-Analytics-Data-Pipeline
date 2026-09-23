select
    order_item_id,
    source_item_total,
    net_sales_amount
from {{ ref('int_order_items_enriched') }}
where abs(source_item_total - net_sales_amount) > 0.02
