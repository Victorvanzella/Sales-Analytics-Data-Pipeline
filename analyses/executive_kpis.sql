select
    count(distinct order_id) as total_orders,
    count(distinct customer_sk) as active_customers,
    sum(quantity) as units,
    round(sum(recognized_revenue), 2) as recognized_revenue,
    round(sum(returned_amount), 2) as returned_amount,
    round(sum(margin_amount) filter (where order_status = 'Delivered'), 2)
        as recognized_margin
from {{ ref('fct_sales') }}
