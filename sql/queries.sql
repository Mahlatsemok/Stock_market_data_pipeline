-- PostgreSQL warehouse analysis queries.

-- Number of daily observations and date coverage by ticker.
SELECT
    ticker,
    COUNT(*) AS total_records,
    MIN(date) AS first_date,
    MAX(date) AS last_date
FROM daily_performance
GROUP BY ticker
ORDER BY total_records DESC;

-- Highest closing prices in the warehouse.
SELECT ticker, date, close
FROM daily_performance
ORDER BY close DESC
LIMIT 10;

-- Highest-volume trading days.
SELECT ticker, date, volume
FROM daily_performance
ORDER BY volume DESC
LIMIT 10;

-- Latest summary for each ticker.
SELECT
    ticker,
    latest_date,
    latest_close,
    average_daily_return,
    volatility,
    total_records
FROM ticker_summary
ORDER BY average_daily_return DESC NULLS LAST;

-- Best average daily returns among tickers with at least one return.
SELECT ticker, average_daily_return, volatility
FROM ticker_summary
WHERE average_daily_return IS NOT NULL
ORDER BY average_daily_return DESC
LIMIT 10;

-- Daily observations for one ticker, including technical indicators.
SELECT date, close, daily_return, ma5, ma20
FROM daily_performance
WHERE ticker = 'AAPL'
ORDER BY date;
