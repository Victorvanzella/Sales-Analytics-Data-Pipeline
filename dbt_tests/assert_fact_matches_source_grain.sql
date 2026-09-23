with source_count as (
    select count(*) as rows from {{ source('raw', 'order_items') }}
),

fact_count as (
    select count(*) as rows from {{ ref('fct_sales') }}
)

select source_count.rows as source_rows, fact_count.rows as fact_rows
from source_count
cross join fact_count
where source_count.rows != fact_count.rows
