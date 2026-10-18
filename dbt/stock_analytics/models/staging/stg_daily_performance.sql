select
    ticker,
    date,
    open,
    high,
    low,
    close,
    volume,
    adj_close,
    daily_return,
    ma5,
    ma20,
    year,
    month
from {{ source('stock_warehouse', 'daily_performance') }}
where ticker is not null
  and date is not null
