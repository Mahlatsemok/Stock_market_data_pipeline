select
    ticker,
    date,
    year,
    month,
    open,
    high,
    low,
    close,
    volume,
    adj_close,
    daily_return,
    ma5,
    ma20,
    case
        when daily_return is null then 'first_observation'
        when daily_return > 0 then 'gain'
        when daily_return < 0 then 'loss'
        else 'unchanged'
    end as daily_return_direction,
    case
        when ma20 is null then null
        else close >= ma20
    end as close_at_or_above_ma20
from {{ ref('stg_daily_performance') }}
