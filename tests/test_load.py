
import pandas as pd
import pytest

import stock_pipeline.load.postgres as postgres_module


@pytest.fixture
def sample_stock_data():
    return pd.DataFrame({
        "Date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
        "Ticker": ["AAPL", "AAPL"],
        "Open": [100.0, 101.0],
        "High": [102.0, 103.0],
        "Low": [99.0, 100.0],
        "Close": [101.0, 102.0],
        "Volume": [1000, 1100],
    })


def test_load_to_postgres_appends_data_to_stocks_table(
    sample_stock_data, monkeypatch
):
    fake_engine = object()
    engine_calls = []
    load_calls = []

    def fake_create_engine(connection_string):
        engine_calls.append(connection_string)
        return fake_engine

    def fake_to_sql(self, **kwargs):
        load_calls.append({
            "data": self.copy(),
            **kwargs,
        })

    monkeypatch.setattr(
        postgres_module, "create_engine", fake_create_engine
    )
    monkeypatch.setattr(pd.DataFrame, "to_sql", fake_to_sql)

    postgres_module.load_to_postgres(
        sample_stock_data,
        "postgresql://test:test@localhost:5432/test_db",
    )

    assert engine_calls == [
        "postgresql://test:test@localhost:5432/test_db"
    ]
    assert len(load_calls) == 1

    call = load_calls[0]
    assert call["name"] == "stocks"
    assert call["con"] is fake_engine
    assert call["if_exists"] == "append"
    assert call["index"] is False
    assert call["method"] == "multi"
    pd.testing.assert_frame_equal(call["data"], sample_stock_data)


def test_load_to_postgres_handles_empty_dataframe(
    monkeypatch,
):
    fake_engine = object()
    load_calls = []

    monkeypatch.setattr(
        postgres_module,
        "create_engine",
        lambda connection_string: fake_engine,
    )

    def fake_to_sql(self, **kwargs):
        load_calls.append({
            "row_count": len(self),
            **kwargs,
        })

    monkeypatch.setattr(pd.DataFrame, "to_sql", fake_to_sql)

    empty_data = pd.DataFrame(columns=[
        "Date", "Ticker", "Open", "High",
        "Low", "Close", "Volume",
    ])

    postgres_module.load_to_postgres(
        empty_data,
        "postgresql://test:test@localhost:5432/test_db",
    )

    assert len(load_calls) == 1
    assert load_calls[0]["row_count"] == 0
    assert load_calls[0]["name"] == "stocks"


def test_load_to_postgres_propagates_database_errors(
    sample_stock_data, monkeypatch
):
    monkeypatch.setattr(
        postgres_module,
        "create_engine",
        lambda connection_string: object(),
    )

    def failing_to_sql(self, **kwargs):
        raise RuntimeError("Database connection failed")

    monkeypatch.setattr(pd.DataFrame, "to_sql", failing_to_sql)

    with pytest.raises(
        RuntimeError, match="Database connection failed"
    ):
        postgres_module.load_to_postgres(
            sample_stock_data,
            "postgresql://test:test@localhost:5432/test_db",
        )
        