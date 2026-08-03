-- ============================================
-- STOCK MARKET DATA ANALYSIS
-- ============================================


-- Count records for each stock

SELECT
    Ticker,
    COUNT(*) AS total_records
FROM stocks
GROUP BY Ticker;
GROUP BY total_records DESC;


-- Highest closing price

SELECT
    Ticker,
    MAX(Close) AS highest_closing_price
FROM stocks
GROUP BY Ticker
ORDER BY highest_closing_price DESC;


-- Lowest closing price

SELECT
    Ticker,
    MIN(Close) AS lowest_closing_price
FROM stocks
GROUP BY Ticker
ORDER BY lowest_closing_price ASC;


-- Average closing price

SELECT
    Ticker,
    AVG(Close) AS average_closing_price
FROM stocks
GROUP BY Ticker
ORDER BY average_closing_price DESC;


-- Average trading volume

SELECT
    Ticker,
    AVG(Volume) AS average_trading_volume
FROM stocks
GROUP BY Ticker
ORDER BY average_trading_volume DESC;


-- Best daily return

SELECT
    Ticker,
    MAX(Daily_Return) AS best_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY best_daily_return DESC;


-- Worst daily return

SELECT
    Ticker,
    MIN(Daily_Return) AS worst_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY worst_daily_return ASC;


-- Average daily return

SELECT
    Ticker,
    AVG(Daily_Return) AS average_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY average_daily_return DESC;


-- Daily return volatility per stock

SELECT
    Ticker,
    AVG(Daily_Return) AS average_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY average_daily_return DESC;


-- Highest closing price across all stocks

SELECT
    Ticker,
    Date,
    Close
FROM stocks
ORDER BY Close DESC
LIMIT 10;


-- Highest trading volume days

SELECT
    Ticker,
    Date,
    Volume
FROM stocks
ORDER BY Volume DESC
LIMIT 10;


-- Best performing stock

SELECT
    Ticker,
    AVG(Daily_Return) AS average_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY average_daily_return DESC
LIMIT 1;
