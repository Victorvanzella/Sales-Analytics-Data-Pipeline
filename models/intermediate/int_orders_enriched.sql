with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

items as (
    select * from {{ ref('int_order_items_enriched') }}
),

order_totals as (
    select
        order_id,
        count(*) as item_lines,
        sum(quantity) as units,
        round(sum(gross_sales_amount), 2) as gross_sales_amount,
        round(sum(discount_amount), 2) as discount_amount,
        round(sum(net_sales_amount), 2) as net_sales_amount,
        round(sum(cost_amount), 2) as cost_amount,
        round(sum(margin_amount), 2) as margin_amount
    from items
    group by order_id
)

select
    orders.order_id,
    orders.order_date,
    orders.order_status,
    orders.payment_method,
    orders.sales_channel,
    orders.shipping_country,
    customers.customer_id,
    customers.customer_name,
    customers.segment as customer_segment,
    customers.city,
    customers.state,
    order_totals.item_lines,
    order_totals.units,
    order_totals.gross_sales_amount,
    order_totals.discount_amount,
    order_totals.net_sales_amount,
    order_totals.cost_amount,
    order_totals.margin_amount,
    greatest(orders._ingested_at, customers._ingested_at) as _ingested_at
from orders
inner join customers on orders.customer_id = customers.customer_id
inner join order_totals on orders.order_id = order_totals.order_id
