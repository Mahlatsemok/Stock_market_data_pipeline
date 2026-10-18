with monthly_metrics as (
    select
        ticker,
        year,
        month,
        min(date) as first_trading_date,
        max(date) as last_trading_date,
        (array_agg(close order by date))[1] as first_close,
        (array_agg(close order by date desc))[1] as last_close,
        max(high) as highest_price,
        min(low) as lowest_price,
        sum(volume) as total_volume,
        count(*) as trading_days,
        avg(daily_return) as average_daily_return
    from {{ ref('stg_daily_performance') }}
    group by ticker, year, month
), with_prior_month as (
    select
        *,
        lag(last_close) over (
            partition by ticker
            order by year, month
        ) as prior_month_close
    from monthly_metrics
)

select
    ticker,
    year,
    month,
    first_trading_date,
    last_trading_date,
    first_close,
    last_close,
    (last_close / nullif(prior_month_close, 0) - 1) * 100
        as monthly_return_pct,
    highest_price,
    lowest_price,
    total_volume,
    trading_days,
    average_daily_return
from monthly_metrics
