select ticker, year, month
from {{ ref('agg_monthly_performance') }}
group by ticker, year, month
having count(*) > 1
