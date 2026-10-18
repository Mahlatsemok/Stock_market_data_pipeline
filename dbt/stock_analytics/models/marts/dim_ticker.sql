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
    volatility,
    dense_rank() over (
        order by average_daily_return desc nulls last
    ) as average_return_rank
from {{ ref('stg_ticker_summary') }}
