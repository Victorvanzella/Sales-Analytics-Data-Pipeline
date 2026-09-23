select
    order_date,
    count(distinct order_id) as orders,
    count(distinct case when order_status = 'Delivered' then order_id end) as delivered_orders,
    count(distinct customer_sk) as active_customers,
    sum(quantity) as units,
    round(sum(gross_sales_amount), 2) as gross_sales_amount,
    round(sum(discount_amount), 2) as discount_amount,
    round(sum(net_sales_amount), 2) as net_sales_amount,
    round(sum(recognized_revenue), 2) as recognized_revenue,
    round(sum(returned_amount), 2) as returned_amount,
    round(
        sum(recognized_revenue)
        / nullif(count(distinct case when order_status = 'Delivered' then order_id end), 0),
        2
    ) as average_delivered_order_value
from {{ ref('fct_sales') }}
group by order_date
