select ticker, date
from {{ ref('fct_daily_performance') }}
group by ticker, date
having count(*) > 1
