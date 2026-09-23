select
    date_trunc('month', order_date)::date as month_start,
    count(distinct order_id) as orders,
    count(distinct customer_sk) as active_customers,
    sum(quantity) as units,
    round(sum(recognized_revenue), 2) as recognized_revenue,
    round(sum(margin_amount) filter (where order_status = 'Delivered'), 2) as recognized_margin,
    round(sum(discount_amount), 2) as discount_amount,
    round(sum(returned_amount), 2) as returned_amount
from {{ ref('fct_sales') }}
group by date_trunc('month', order_date)
