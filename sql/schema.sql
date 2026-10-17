-- PostgreSQL warehouse tables for Spark Gold datasets.
-- Safe to run repeatedly; natural keys make reloads idempotent.

CREATE TABLE IF NOT EXISTS daily_performance (
    ticker              VARCHAR(16) NOT NULL,
    date                DATE NOT NULL,
    open                NUMERIC(20, 6) NOT NULL,
    high                NUMERIC(20, 6) NOT NULL,
    low                 NUMERIC(20, 6) NOT NULL,
    close               NUMERIC(20, 6) NOT NULL,
    volume              BIGINT NOT NULL,
    adj_close           NUMERIC(20, 6),
    daily_return        DOUBLE PRECISION,
    ma5                 DOUBLE PRECISION,
    ma20                DOUBLE PRECISION,
    year                SMALLINT NOT NULL,
    month               SMALLINT NOT NULL,
    PRIMARY KEY (ticker, date),
    CHECK (volume >= 0),
    CHECK (month BETWEEN 1 AND 12)
);

CREATE INDEX IF NOT EXISTS idx_daily_performance_date
    ON daily_performance (date);

CREATE TABLE IF NOT EXISTS ticker_summary (
    ticker                  VARCHAR(16) PRIMARY KEY,
    total_records           BIGINT NOT NULL,
    first_date              DATE NOT NULL,
    last_date               DATE NOT NULL,
    latest_date             DATE NOT NULL,
    latest_close            DOUBLE PRECISION NOT NULL,
    latest_volume           BIGINT NOT NULL,
    highest_close           DOUBLE PRECISION NOT NULL,
    lowest_close            DOUBLE PRECISION NOT NULL,
    average_close           DOUBLE PRECISION NOT NULL,
    average_volume          DOUBLE PRECISION NOT NULL,
    best_daily_return       DOUBLE PRECISION,
    worst_daily_return      DOUBLE PRECISION,
    average_daily_return    DOUBLE PRECISION,
    volatility              DOUBLE PRECISION
);
