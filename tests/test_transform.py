
import pandas as pd
import pytest

from stock_pipeline.transform.stocks import transform_stock_data


@pytest.fixture
def sample_stock_data():
    return pd.DataFrame({
        "Date": pd.to_datetime([
            "2025-01-03",
            "2025-01-01",
            "2025-01-02",
            "2025-01-02",
            "2025-01-04",
        ]),
        "Open": [103.0, 100.0, 101.0, 101.0, None],
        "High": [105.0, 102.0, 103.0, 103.0, 106.0],
        "Low": [102.0, 99.0, 100.0, 100.0, 104.0],
        "Close": [104.0, 101.0, 102.0, 102.0, 105.0],
        "Volume": [1200, 1000, 1100, 1100, 1300],
    })


def test_transform_removes_duplicates_and_missing_values(
    sample_stock_data, tmp_path, monkeypatch
):
    import stock_pipeline.transform.stocks as stocks_module

    monkeypatch.setattr(stocks_module, "PROCESSED_DATA_DIR", tmp_path)

    result = transform_stock_data(sample_stock_data, "AAPL")

    assert len(result) == 3
    assert result["Ticker"].eq("AAPL").all()
    assert result["Date"].is_monotonic_increasing
    assert not result.duplicated(subset=["Ticker", "Date"]).any()
    assert result[["Open", "High", "Low", "Close", "Volume"]].notna().all().all()


def test_transform_calculates_daily_return_and_moving_averages(
    tmp_path, monkeypatch
):
    import stock_pipeline.transform.stocks as stocks_module

    monkeypatch.setattr(stocks_module, "PROCESSED_DATA_DIR", tmp_path)

    dates = pd.date_range("2025-01-01", periods=21, freq="D")
    closes = list(range(100, 121))

    df = pd.DataFrame({
        "Date": dates,
        "Open": closes,
        "High": [price + 2 for price in closes],
        "Low": [price - 2 for price in closes],
        "Close": closes,
        "Volume": [1000] * len(closes),
    })

    result = transform_stock_data(df, "AAPL")

    assert result["Daily_Return"].iloc[1] == pytest.approx(
        (101 / 100 - 1) * 100
    )
    assert pd.isna(result["MA5"].iloc[3])
    assert result["MA5"].iloc[4] == pytest.approx(102.0)
    assert pd.isna(result["MA20"].iloc[18])
    assert result["MA20"].iloc[19] == pytest.approx(109.5)


def test_transform_saves_processed_csv(tmp_path, monkeypatch):
    import stock_pipeline.transform.stocks as stocks_module

    monkeypatch.setattr(stocks_module, "PROCESSED_DATA_DIR", tmp_path)

    df = pd.DataFrame({
        "Date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
        "Open": [100.0, 101.0],
        "High": [102.0, 103.0],
        "Low": [99.0, 100.0],
        "Close": [101.0, 102.0],
        "Volume": [1000, 1100],
    })

    transform_stock_data(df, "MSFT")

    output_file = tmp_path / "MSFT_stock_clean.csv"

    assert output_file.exists()

    saved_data = pd.read_csv(output_file)

    assert len(saved_data) == 2
    assert "Daily_Return" in saved_data.columns
    assert "MA5" in saved_data.columns
    assert "MA20" in saved_data.columns


def test_transform_handles_multiindex_columns(tmp_path, monkeypatch):
    import stock_pipeline.transform.stocks as stocks_module

    monkeypatch.setattr(stocks_module, "PROCESSED_DATA_DIR", tmp_path)

    columns = pd.MultiIndex.from_tuples([
        ("Open", "AAPL"),
        ("High", "AAPL"),
        ("Low", "AAPL"),
        ("Close", "AAPL"),
        ("Volume", "AAPL"),
    ])

    df = pd.DataFrame(
        [[100.0, 102.0, 99.0, 101.0, 1000],
         [101.0, 103.0, 100.0, 102.0, 1100]],
        index=pd.to_datetime(["2025-01-01", "2025-01-02"]),
        columns=columns,
    )
    df.index.name = "Date"

    result = transform_stock_data(df, "AAPL")

    assert "Date" in result.columns
    assert "Ticker" in result.columns
    assert result["Ticker"].eq("AAPL").all()
    assert len(result) == 2


def test_transform_rejects_invalid_prices_without_saving(
    tmp_path, monkeypatch
):
    import stock_pipeline.transform.stocks as stocks_module

    monkeypatch.setattr(
        stocks_module,
        "PROCESSED_DATA_DIR",
        tmp_path,
    )

    df = pd.DataFrame({
        "Date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
        "Open": [100.0, 101.0],
        "High": [102.0, 103.0],
        "Low": [99.0, 100.0],
        "Close": [101.0, -1.0],
        "Volume": [1000, 1100],
    })

    with pytest.raises(ValueError, match="Invalid price"):
        transform_stock_data(df, "AAPL")

    assert not (tmp_path / "AAPL_stock_clean.csv").exists()
