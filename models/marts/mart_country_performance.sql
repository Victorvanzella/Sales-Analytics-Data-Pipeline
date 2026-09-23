with performance as (
    select
        shipping_country as country,
        count(distinct order_id) as orders,
        round(sum(recognized_revenue), 2) as recognized_revenue
    from {{ ref('fct_sales') }}
    group by shipping_country
),

totals as (
    select sum(recognized_revenue) as total_revenue from performance
)

select
    performance.country,
    performance.orders,
    performance.recognized_revenue,
    round(100 * performance.recognized_revenue / nullif(totals.total_revenue, 0), 2)
        as actual_revenue_share_pct,
    targets.target_revenue_share_pct,
    round(
        100 * performance.recognized_revenue / nullif(totals.total_revenue, 0)
        - targets.target_revenue_share_pct,
        2
    ) as variance_to_target_pct
from performance
cross join totals
left join {{ ref('country_targets') }} as targets on performance.country = targets.country
