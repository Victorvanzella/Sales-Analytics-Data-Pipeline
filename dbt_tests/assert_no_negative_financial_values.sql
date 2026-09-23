select *
from {{ ref('fct_sales') }}
where
    gross_sales_amount < 0
    or discount_amount < 0
    or net_sales_amount < 0
    or cost_amount < 0
    or recognized_revenue < 0
    or returned_amount < 0
