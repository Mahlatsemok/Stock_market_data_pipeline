select
    ticker,
    total_records,
    daily_record_count
from (
    select
        d.ticker,
        d.total_records,
        count(f.date) as daily_record_count
    from {{ ref('dim_ticker') }} as d
    left join {{ ref('fct_daily_performance') }} as f
        on d.ticker = f.ticker
    group by d.ticker, d.total_records
) as ticker_counts
where total_records <> daily_record_count
