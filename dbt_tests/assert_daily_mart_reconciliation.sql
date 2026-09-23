with fact_total as (
    select round(sum(recognized_revenue), 2) as revenue from {{ ref('fct_sales') }}
),

mart_total as (
    select round(sum(recognized_revenue), 2) as revenue from {{ ref('mart_daily_sales') }}
)

select fact_total.revenue as fact_revenue, mart_total.revenue as mart_revenue
from fact_total
cross join mart_total
where abs(fact_total.revenue - mart_total.revenue) > 0.02
