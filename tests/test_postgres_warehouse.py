from contextlib import contextmanager
from datetime import date

import pandas as pd
import pytest

import stock_pipeline.load.postgres as postgres_module


def test_database_record_conversion_maps_gold_columns_and_nulls():
    daily = pd.DataFrame({
        "Ticker": ["AAPL"],
        "Date": [pd.Timestamp("2025-01-02")],
        "Open": [101.0],
        "High": [103.0],
        "Low": [100.0],
        "Close": [102.0],
        "Volume": [1100],
        "Daily_Return": [pd.NA],
        "MA5": [pd.NA],
        "MA20": [pd.NA],
        "Year": [2025],
        "Month": [1],
    })

    record = postgres_module._to_database_records(
        daily,
        postgres_module.DAILY_COLUMN_MAP,
        optional_columns={"adj_close"},
    )[0]

    assert record["ticker"] == "AAPL"
    assert record["date"] == date(2025, 1, 2)
    assert record["volume"] == 1100
    assert record["adj_close"] is None
    assert record["daily_return"] is None


def test_database_record_conversion_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        postgres_module._to_database_records(
            pd.DataFrame({"Ticker": ["AAPL"]}),
            postgres_module.DAILY_COLUMN_MAP,
            optional_columns={"adj_close"},
        )


def test_gold_loader_initializes_schema_and_upserts_both_datasets(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.statements = []

        def exec_driver_sql(self, statement):
            self.statements.append(statement)

        def execute(self, statement, records):
            self.statements.append((statement, records))

    connection = FakeConnection()

    class FakeEngine:
        @contextmanager
        def begin(self):
            yield connection

        def dispose(self):
            pass

    engine = FakeEngine()
    monkeypatch.setattr(
        postgres_module,
        "create_engine",
        lambda *_args, **_kwargs: engine,
    )

    daily = pd.DataFrame({
        "Ticker": ["AAPL"],
        "Date": [pd.Timestamp("2025-01-02")],
        "Open": [101.0],
        "High": [103.0],
        "Low": [100.0],
        "Close": [102.0],
        "Volume": [1100],
        "Adj Close": [102.0],
        "Daily_Return": [1.0],
        "MA5": [None],
        "MA20": [None],
        "Year": [2025],
        "Month": [1],
    })
    summary = pd.DataFrame({
        "Ticker": ["AAPL"],
        "total_records": [1],
        "first_date": [pd.Timestamp("2025-01-02")],
        "last_date": [pd.Timestamp("2025-01-02")],
        "latest_date": [pd.Timestamp("2025-01-02")],
        "latest_close": [102.0],
        "latest_volume": [1100],
        "highest_close": [102.0],
        "lowest_close": [102.0],
        "average_close": [102.0],
        "average_volume": [1100.0],
        "best_daily_return": [1.0],
        "worst_daily_return": [1.0],
        "average_daily_return": [1.0],
        "volatility": [None],
    })

    loaded = postgres_module.load_gold_to_postgres(
        daily,
        summary,
        "postgresql+psycopg://user:pass@localhost:5432/stocks",
    )

    assert loaded == (1, 1)
    executions = [
        item for item in connection.statements if isinstance(item, tuple)
    ]
    assert len(executions) == 2
    assert "ON CONFLICT (ticker, date)" in str(executions[0][0])
    assert "ON CONFLICT (ticker)" in str(executions[1][0])
