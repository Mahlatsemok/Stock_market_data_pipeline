
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

@pytest.mark.parametrize(
    "ticker",
    ["", "   ", None, 123],
)
def test_extraction_rejects_invalid_ticker(ticker):
    with pytest.raises(
        ValueError,
        match="ticker must be a non-empty string",
    ):
        yahoo_module.extract_stock_data(ticker)


@pytest.mark.parametrize(
    "period",
    ["", "   ", None],
)


def test_extraction_rejects_invalid_period(period):
    with pytest.raises(
        ValueError,
        match="period must be a non-empty string",
    ):
        yahoo_module.extract_stock_data("AAPL", period=period)


@pytest.mark.parametrize(
    "max_retries",
    [0, -1, 1.5, "3", True],
)


def test_extraction_rejects_invalid_max_retries(max_retries):
    with pytest.raises(
        ValueError,
        match="max_retries must be a positive integer",
    ):
        yahoo_module.extract_stock_data(
            "AAPL",
            max_retries=max_retries,
        )


def test_extraction_retries_after_none_response(
    sample_yahoo_data, tmp_path, monkeypatch
):
    monkeypatch.setattr(yahoo_module, "RAW_DATA_DIR", tmp_path)

    calls = {"count": 0}

    def download_with_none_response(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            return None

        return sample_yahoo_data.copy()

    monkeypatch.setattr(
        yahoo_module.yf,
        "download",
        download_with_none_response,
    )
    monkeypatch.setattr(yahoo_module.time, "sleep", lambda *_: None)

    result = yahoo_module.extract_stock_data("AAPL")

    assert not result.empty
    assert result["Ticker"].eq("AAPL").all()
    assert calls["count"] == 2
    assert (tmp_path / "AAPL_stock.csv").exists()

def test_extraction_creates_missing_raw_data_directory(
    sample_yahoo_data, tmp_path, monkeypatch
):
    raw_data_dir = tmp_path / "missing" / "raw"
    monkeypatch.setattr(yahoo_module, "RAW_DATA_DIR", raw_data_dir)
    monkeypatch.setattr(
        yahoo_module.yf,
        "download",
        lambda *args, **kwargs: sample_yahoo_data.copy(),
    )

    result = yahoo_module.extract_stock_data("AAPL")

    assert not result.empty
    assert raw_data_dir.is_dir()
    assert (raw_data_dir / "AAPL_stock.csv").exists()

def test_extraction_retries_after_missing_required_columns(
    sample_yahoo_data, tmp_path, monkeypatch
):
    monkeypatch.setattr(yahoo_module, "RAW_DATA_DIR", tmp_path)

    calls = {"count": 0}

    def download_with_missing_columns(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            return sample_yahoo_data.drop(columns=["Close"])

        return sample_yahoo_data.copy()

    monkeypatch.setattr(
        yahoo_module.yf,
        "download",
        download_with_missing_columns,
    )
    monkeypatch.setattr(yahoo_module.time, "sleep", lambda *_: None)

    result = yahoo_module.extract_stock_data("AAPL")

    assert not result.empty
    assert "Close" in result.columns
    assert result["Ticker"].eq("AAPL").all()
    assert calls["count"] == 2
    assert (tmp_path / "AAPL_stock.csv").exists()

def test_extraction_retries_after_empty_dataframe(
    sample_yahoo_data, tmp_path, monkeypatch
):
    monkeypatch.setattr(yahoo_module, "RAW_DATA_DIR", tmp_path)

    calls = {"count": 0}

    def download_with_empty_response(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            return pd.DataFrame()

        return sample_yahoo_data.copy()

    monkeypatch.setattr(
        yahoo_module.yf,
        "download",
        download_with_empty_response,
    )
    monkeypatch.setattr(yahoo_module.time, "sleep", lambda *_: None)

    result = yahoo_module.extract_stock_data("AAPL")

    assert not result.empty
    assert result["Ticker"].eq("AAPL").all()
    assert calls["count"] == 2
    assert (tmp_path / "AAPL_stock.csv").exists()

@pytest.mark.parametrize(
    "retry_delay",
    [-1, -0.5, float("inf"), float("-inf"), float("nan"), True, "2"],
)
def test_extraction_rejects_invalid_retry_delay(retry_delay):
    with pytest.raises(
        ValueError,
        match="retry_delay must be a finite, non-negative number",
    ):
        yahoo_module.extract_stock_data(
            "AAPL",
            retry_delay=retry_delay,
        )


def test_extraction_uses_configured_retry_delay(monkeypatch):
    calls = {"count": 0}
    recorded_delays = []

    def failed_download(*args, **kwargs):
        calls["count"] += 1
        raise ConnectionError("Temporary network failure")

    monkeypatch.setattr(
        yahoo_module.yf,
        "download",
        failed_download,
    )
    monkeypatch.setattr(
        yahoo_module.time,
        "sleep",
        recorded_delays.append,
    )

    result = yahoo_module.extract_stock_data(
        "AAPL",
        max_retries=3,
        retry_delay=0.5,
    )

    assert result.empty
    assert calls["count"] == 3
    assert recorded_delays == [0.5, 0.5]
