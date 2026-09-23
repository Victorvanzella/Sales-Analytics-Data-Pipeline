with order_metrics as (
    select
        customer_sk,
        count(distinct order_id) as lifetime_orders,
        sum(quantity) as lifetime_units,
        round(sum(recognized_revenue), 2) as lifetime_revenue,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        round(
            sum(recognized_revenue)
            / nullif(count(distinct case when order_status = 'Delivered' then order_id end), 0),
            2
        ) as average_order_value
    from {{ ref('fct_sales') }}
    group by customer_sk
),

reference_date as (
    select max(order_date) as max_order_date from {{ ref('fct_sales') }}
)

select
    customers.customer_sk,
    customers.customer_id,
    customers.customer_name,
    customers.segment,
    customers.city,
    customers.state,
    customers.country,
    coalesce(metrics.lifetime_orders, 0) as lifetime_orders,
    coalesce(metrics.lifetime_units, 0) as lifetime_units,
    coalesce(metrics.lifetime_revenue, 0) as lifetime_revenue,
    metrics.first_order_date,
    metrics.last_order_date,
    metrics.average_order_value,
    date_diff('day', metrics.last_order_date, reference_date.max_order_date) as recency_days,
    case
        when coalesce(metrics.lifetime_revenue, 0) >= 10000 then 'Platinum'
        when coalesce(metrics.lifetime_revenue, 0) >= 5000 then 'Gold'
        when coalesce(metrics.lifetime_revenue, 0) >= 1500 then 'Silver'
        else 'Bronze'
    end as customer_tier
from {{ ref('dim_customer') }} as customers
left join order_metrics as metrics on customers.customer_sk = metrics.customer_sk
cross join reference_date
