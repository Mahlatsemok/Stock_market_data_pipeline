
import pandas as pd
import pytest

import stock_pipeline.bronze.ingestion as bronze_module


@pytest.fixture
def sample_stock_data():
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000, 1100],
            "Ticker": ["AAPL", "AAPL"],
        },
        index=pd.to_datetime(
            ["2025-01-01", "2025-01-02"]
        ),
    )


def test_ingestion_saves_snapshot_with_metadata(
    sample_stock_data, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        bronze_module, "BRONZE_DATA_DIR", tmp_path
    )

    original = sample_stock_data.copy(deep=True)

    output_file = bronze_module.ingest_to_bronze(
        sample_stock_data, "AAPL"
    )

    assert output_file.exists()
    assert output_file.parent == tmp_path
    assert output_file.name.startswith("AAPL_")

    saved = pd.read_csv(output_file)

    assert len(saved) == 2
    assert "Date" in saved.columns
    assert saved["Ticker"].eq("AAPL").all()
    assert saved["source_system"].eq("yahoo_finance").all()
    assert saved["ingested_at_utc"].notna().all()

    pd.testing.assert_frame_equal(sample_stock_data, original)


def test_repeated_ingestion_creates_separate_snapshots(
    sample_stock_data, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        bronze_module, "BRONZE_DATA_DIR", tmp_path
    )

    first = bronze_module.ingest_to_bronze(
        sample_stock_data, "AAPL"
    )
    second = bronze_module.ingest_to_bronze(
        sample_stock_data, "AAPL"
    )

    assert first != second
    assert first.exists()
    assert second.exists()
    assert len(list(tmp_path.glob("AAPL_*.csv"))) == 2


@pytest.mark.parametrize(
    ("df", "ticker", "source", "message"),
    [
        (pd.DataFrame(), "AAPL", "yahoo_finance", "empty"),
        (pd.DataFrame({"Close": [100]}), "", "yahoo_finance", "ticker"),
        (pd.DataFrame({"Close": [100]}), "../AAPL", "yahoo_finance", "characters"),
        (pd.DataFrame({"Close": [100]}), "AAPL", "", "source"),
    ],
)
def test_invalid_ingestion_inputs_are_rejected(
    df, ticker, source, message, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        bronze_module, "BRONZE_DATA_DIR", tmp_path
    )

    with pytest.raises(ValueError, match=message):
        bronze_module.ingest_to_bronze(
            df, ticker, source=source
        )


def test_ingestion_rejects_non_dataframe():
    with pytest.raises(ValueError, match="pandas DataFrame"):
        bronze_module.ingest_to_bronze([], "AAPL")
