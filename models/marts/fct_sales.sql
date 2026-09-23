{{
    config(
        materialized='incremental',
        unique_key='order_item_id',
        incremental_strategy='delete+insert',
        on_schema_change='fail'
    )
}}

with items as (
    select * from {{ ref('int_order_items_enriched') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
)

select
    md5(items.order_item_id) as sales_sk,
    items.order_item_id,
    orders.order_id,
    cast(strftime(orders.order_date, '%Y%m%d') as integer) as date_key,
    md5(orders.customer_id) as customer_sk,
    md5(items.product_id) as product_sk,
    orders.order_date,
    orders.order_status,
    orders.payment_method,
    orders.sales_channel,
    orders.shipping_country,
    items.quantity,
    items.unit_price,
    items.discount_pct,
    items.gross_sales_amount,
    items.discount_amount,
    items.net_sales_amount,
    items.cost_amount,
    items.margin_amount,
    case
        when orders.order_status = '{{ var("recognized_order_status") }}'
            then items.net_sales_amount
        else 0
    end as recognized_revenue,
    case when orders.order_status = 'Returned' then items.net_sales_amount else 0 end
        as returned_amount,
    greatest(orders.updated_at, items.updated_at) as source_updated_at,
    greatest(orders._ingested_at, items._ingested_at) as source_ingested_at
from items
inner join orders on items.order_id = orders.order_id
{% if is_incremental() %}
where greatest(orders.updated_at, items.updated_at) > (
    select coalesce(max(source_updated_at), timestamp '1900-01-01') from {{ this }}
)
{% endif %}
