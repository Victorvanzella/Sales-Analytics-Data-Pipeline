select
    products.category,
    products.subcategory,
    count(distinct sales.order_id) as orders,
    sum(sales.quantity) as units,
    round(sum(sales.recognized_revenue), 2) as recognized_revenue,
    round(sum(sales.margin_amount) filter (where sales.order_status = 'Delivered'), 2)
        as recognized_margin,
    round(
        100 * sum(sales.margin_amount) filter (where sales.order_status = 'Delivered')
        / nullif(sum(sales.recognized_revenue), 0),
        2
    ) as margin_pct
from {{ ref('fct_sales') }} as sales
inner join {{ ref('dim_product') }} as products on sales.product_sk = products.product_sk
group by products.category, products.subcategory
