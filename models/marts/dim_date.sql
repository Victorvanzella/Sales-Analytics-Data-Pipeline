with bounds as (
    select
        min(order_date)::date as start_date,
        max(order_date)::date as end_date
    from {{ ref('stg_orders') }}
),

date_spine as (
    select cast(date_value as date) as date_day
    from bounds,
        unnest(generate_series(start_date, end_date, interval 1 day)) as dates(date_value)
)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
    date_day,
    extract(year from date_day)::integer as year_number,
    extract(quarter from date_day)::integer as quarter_number,
    extract(month from date_day)::integer as month_number,
    strftime(date_day, '%B') as month_name,
    extract(week from date_day)::integer as week_number,
    extract(dayofweek from date_day)::integer as day_of_week_number,
    strftime(date_day, '%A') as day_name,
    case when extract(dayofweek from date_day) in (0, 6) then true else false end as is_weekend
from date_spine
