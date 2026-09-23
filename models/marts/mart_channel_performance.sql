select
    sales_channel,
    payment_method,
    count(distinct order_id) as orders,
    count(distinct customer_sk) as customers,
    sum(quantity) as units,
    round(sum(recognized_revenue), 2) as recognized_revenue,
    round(sum(returned_amount), 2) as returned_amount,
    round(
        sum(recognized_revenue)
        / nullif(count(distinct case when order_status = 'Delivered' then order_id end), 0),
        2
    ) as average_delivered_order_value
from {{ ref('fct_sales') }}
group by sales_channel, payment_method
