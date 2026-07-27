-- ============================================
-- STOCK MARKET DATA ANALYSIS
-- ============================================


-- 1. Count records for each stock

SELECT
    Ticker,
    COUNT(*) AS total_records
FROM stocks
GROUP BY Ticker;


-- 2. Highest closing price

SELECT
    Ticker,
    MAX(Close) AS highest_closing_price
FROM stocks
GROUP BY Ticker
ORDER BY highest_closing_price DESC;


-- 3. Lowest closing price

SELECT
    Ticker,
    MIN(Close) AS lowest_closing_price
FROM stocks
GROUP BY Ticker
ORDER BY lowest_closing_price ASC;


-- 4. Average closing price

SELECT
    Ticker,
    AVG(Close) AS average_closing_price
FROM stocks
GROUP BY Ticker
ORDER BY average_closing_price DESC;


-- 5. Average trading volume

SELECT
    Ticker,
    AVG(Volume) AS average_trading_volume
FROM stocks
GROUP BY Ticker
ORDER BY average_trading_volume DESC;


-- 6. Best daily return

SELECT
    Ticker,
    MAX(Daily_Return) AS best_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY best_daily_return DESC;


-- 7. Worst daily return

SELECT
    Ticker,
    MIN(Daily_Return) AS worst_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY worst_daily_return ASC;


-- 8. Average daily return

SELECT
    Ticker,
    AVG(Daily_Return) AS average_daily_return
FROM stocks
GROUP BY Ticker
ORDER BY average_daily_return DESC;


-- 9. Highest closing price across all stocks

SELECT
    Ticker,
    Date,
    Close
FROM stocks
ORDER BY Close DESC
LIMIT 10;


-- 10. Highest trading volume days

SELECT
    Ticker,
    Date,
    Volume
FROM stocks
ORDER BY Volume DESC
LIMIT 10;
