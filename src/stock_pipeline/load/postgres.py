from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text


DAILY_COLUMN_MAP = {
    "ticker": "Ticker",
    "date": "Date",
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
    "adj_close": "Adj Close",
    "daily_return": "Daily_Return",
    "ma5": "MA5",
    "ma20": "MA20",
    "year": "Year",
    "month": "Month",
}

SUMMARY_COLUMN_MAP = {
    "ticker": "Ticker",
    "total_records": "total_records",
    "first_date": "first_date",
    "last_date": "last_date",
    "latest_date": "latest_date",
    "latest_close": "latest_close",
    "latest_volume": "latest_volume",
    "highest_close": "highest_close",
    "lowest_close": "lowest_close",
    "average_close": "average_close",
    "average_volume": "average_volume",
    "best_daily_return": "best_daily_return",
    "worst_daily_return": "worst_daily_return",
    "average_daily_return": "average_daily_return",
    "volatility": "volatility",
}

DAILY_UPSERT = text("""
    INSERT INTO daily_performance (
        ticker, date, open, high, low, close, volume, adj_close,
        daily_return, ma5, ma20, year, month
    ) VALUES (
        :ticker, :date, :open, :high, :low, :close, :volume, :adj_close,
        :daily_return, :ma5, :ma20, :year, :month
    )
    ON CONFLICT (ticker, date) DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume,
        adj_close = EXCLUDED.adj_close,
        daily_return = EXCLUDED.daily_return,
        ma5 = EXCLUDED.ma5,
        ma20 = EXCLUDED.ma20,
        year = EXCLUDED.year,
        month = EXCLUDED.month
""")

SUMMARY_UPSERT = text("""
    INSERT INTO ticker_summary (
        ticker, total_records, first_date, last_date, latest_date,
        latest_close, latest_volume, highest_close, lowest_close,
        average_close, average_volume, best_daily_return,
        worst_daily_return, average_daily_return, volatility
    ) VALUES (
        :ticker, :total_records, :first_date, :last_date, :latest_date,
        :latest_close, :latest_volume, :highest_close, :lowest_close,
        :average_close, :average_volume, :best_daily_return,
        :worst_daily_return, :average_daily_return, :volatility
    )
    ON CONFLICT (ticker) DO UPDATE SET
        total_records = EXCLUDED.total_records,
        first_date = EXCLUDED.first_date,
        last_date = EXCLUDED.last_date,
        latest_date = EXCLUDED.latest_date,
        latest_close = EXCLUDED.latest_close,
        latest_volume = EXCLUDED.latest_volume,
        highest_close = EXCLUDED.highest_close,
        lowest_close = EXCLUDED.lowest_close,
        average_close = EXCLUDED.average_close,
        average_volume = EXCLUDED.average_volume,
        best_daily_return = EXCLUDED.best_daily_return,
        worst_daily_return = EXCLUDED.worst_daily_return,
        average_daily_return = EXCLUDED.average_daily_return,
        volatility = EXCLUDED.volatility
""")


def initialize_postgres_schema(engine, schema_path: str | Path | None = None) -> None:
    """Create the warehouse tables and indexes if they do not exist."""
    path = Path(schema_path) if schema_path else (
        Path(__file__).resolve().parents[3] / "sql" / "schema.sql"
    )
    schema_sql = "\n".join(
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    )
    with engine.begin() as connection:
        for statement in schema_sql.split(";"):
            if statement.strip():
                connection.exec_driver_sql(statement)


def _to_database_records(
    frame: pd.DataFrame,
    column_map: dict[str, str],
    *,
    optional_columns: set[str] | None = None,
) -> list[dict[str, Any]]:
    optional = optional_columns or set()
    missing = [
        source
        for target, source in column_map.items()
        if source not in frame.columns and target not in optional
    ]
    if missing:
        raise ValueError(f"Gold dataset is missing required columns: {missing}")

    records: list[dict[str, Any]] = []
    for values in frame.to_dict(orient="records"):
        record: dict[str, Any] = {}
        for target, source in column_map.items():
            value = values.get(source)
            if value is None or pd.isna(value):
                record[target] = None
                continue
            if hasattr(value, "item"):
                value = value.item()
            if isinstance(value, (pd.Timestamp, datetime)):
                value = value.date()
            elif isinstance(value, date):
                value = value
            record[target] = value
        records.append(record)
    return records


def load_gold_to_postgres(
    daily_performance: pd.DataFrame,
    ticker_summary: pd.DataFrame,
    connection_string: str,
) -> tuple[int, int]:
    """Idempotently load Spark Gold frames into the PostgreSQL warehouse."""
    daily_records = _to_database_records(
        daily_performance,
        DAILY_COLUMN_MAP,
        optional_columns={"adj_close"},
    )
    summary_records = _to_database_records(
        ticker_summary,
        SUMMARY_COLUMN_MAP,
    )

    engine = create_engine(connection_string, pool_pre_ping=True)
    try:
        initialize_postgres_schema(engine)
        # Both Gold tables are committed together. Re-running updates the
        # matching ticker/date keys instead of creating duplicate records.
        with engine.begin() as connection:
            if daily_records:
                connection.execute(DAILY_UPSERT, daily_records)
            if summary_records:
                connection.execute(SUMMARY_UPSERT, summary_records)
    finally:
        engine.dispose()

    return len(daily_records), len(summary_records)


def load_to_postgres(
    df: pd.DataFrame,
    connection_string: str
) -> None:
    """
    Load processed stock data into PostgreSQL.
    """

    print("Loading data into PostgreSQL...")

    engine = create_engine(connection_string)

    df.to_sql(
        name="stocks",
        con=engine,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(
        f"Successfully loaded {len(df)} records."
    )
