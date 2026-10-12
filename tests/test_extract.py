
import pandas as pd
import pytest

import stock_pipeline.extract.yahoo_finance as yahoo_module


@pytest.fixture
def sample_yahoo_data():
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000, 1100],
        },
        index=pd.to_datetime(["2025-01-01", "2025-01-02"]),
    )


def test_extraction_saves_downloaded_data(
    sample_yahoo_data, tmp_path, monkeypatch
):
    monkeypatch.setattr(yahoo_module, "RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr(
        yahoo_module.yf,
        "download",
        lambda *args, **kwargs: sample_yahoo_data.copy(),
    )

    result = yahoo_module.extract_stock_data("AAPL", period="10y")

    assert not result.empty
    assert "Ticker" in result.columns
    assert result["Ticker"].eq("AAPL").all()
    assert (tmp_path / "AAPL_stock.csv").exists()


def test_extraction_retries_after_download_failure(
    sample_yahoo_data, tmp_path, monkeypatch
):
    monkeypatch.setattr(yahoo_module, "RAW_DATA_DIR", tmp_path)

    calls = {"count": 0}

    def download_with_retry(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionError("Temporary network failure")
        return sample_yahoo_data.copy()

    monkeypatch.setattr(yahoo_module.yf, "download", download_with_retry)

    if hasattr(yahoo_module, "time"):
        monkeypatch.setattr(yahoo_module.time, "sleep", lambda *_: None)

    result = yahoo_module.extract_stock_data("AAPL", period="10y")

    assert not result.empty
    assert calls["count"] == 2


def test_extraction_returns_empty_dataframe_after_repeated_failures(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(yahoo_module, "RAW_DATA_DIR", tmp_path)

    calls = {"count": 0}

    def failed_download(*args, **kwargs):
        calls["count"] += 1
        raise ConnectionError("Yahoo Finance unavailable")

    monkeypatch.setattr(yahoo_module.yf, "download", failed_download)

    if hasattr(yahoo_module, "time"):
        monkeypatch.setattr(yahoo_module.time, "sleep", lambda *_: None)

    result = yahoo_module.extract_stock_data("AAPL", period="10y")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert calls["count"] == 3
