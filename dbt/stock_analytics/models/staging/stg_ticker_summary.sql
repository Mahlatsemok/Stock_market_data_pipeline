select
    ticker,
    total_records,
    first_date,
    last_date,
    latest_date,
    latest_close,
    latest_volume,
    highest_close,
    lowest_close,
    average_close,
    average_volume,
    best_daily_return,
    worst_daily_return,
    average_daily_return,
    volatility
from {{ source('stock_warehouse', 'ticker_summary') }}
where ticker is not null
