-- 1. Get all stock records
SELECT *
FROM stocks;


-- 2. Find the highest closing price
SELECT MAX(Close) AS highest_closing_price
FROM stocks;


-- 3. Find the lowest closing price
SELECT MIN(Close) AS lowest_closing_price
FROM stocks;


-- 4. Calculate the average closing price
SELECT AVG(Close) AS average_closing_price
FROM stocks;


-- 5. Calculate the average trading volume
SELECT AVG(Volume) AS average_trading_volume
FROM stocks;


-- 6. Find the top 10 highest closing prices
SELECT Date, Close
FROM stocks
ORDER BY Close DESC
LIMIT 10;


-- 7. Find the top 10 highest trading volume days
SELECT Date, Volume
FROM stocks
ORDER BY Volume DESC
LIMIT 10;


-- 8. Find the best daily returns
SELECT Date, Daily_Return
FROM stocks
ORDER BY Daily_Return DESC
LIMIT 10;


-- 9. Find the worst daily returns
SELECT Date, Daily_Return
FROM stocks
ORDER BY Daily_Return ASC
LIMIT 10;
