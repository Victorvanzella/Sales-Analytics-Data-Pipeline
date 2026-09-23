select orders.order_id
from {{ ref('stg_orders') }} as orders
left join {{ ref('stg_order_items') }} as items on orders.order_id = items.order_id
where items.order_id is null
