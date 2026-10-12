
import pandas as pd
import pytest

from stock_pipeline.quality.validation import validate_stock_data


@pytest.fixture
def valid_stock_data():
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(
                ["2026-01-02", "2026-01-05"]
            ),
            "Ticker": ["AAPL", "AAPL"],
            "Open": [100.0, 102.0],
            "High": [105.0, 106.0],
            "Low": [99.0, 101.0],
            "Close": [104.0, 105.0],
            "Volume": [1_000_000, 1_200_000],
        }
    )


def test_valid_stock_data_passes(valid_stock_data):
    assert validate_stock_data(valid_stock_data, "AAPL") is True


def test_empty_dataframe_is_rejected():
    columns = [
        "Date", "Ticker", "Open", "High",
        "Low", "Close", "Volume",
    ]
    df = pd.DataFrame(columns=columns)

    with pytest.raises(ValueError, match="DataFrame is empty"):
        validate_stock_data(df, "AAPL")


def test_missing_required_column_is_rejected(valid_stock_data):
    df = valid_stock_data.drop(columns=["Volume"])

    with pytest.raises(ValueError, match="Missing columns"):
        validate_stock_data(df, "AAPL")


def test_duplicate_ticker_date_is_rejected(valid_stock_data):
    df = pd.concat(
        [valid_stock_data, valid_stock_data.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="duplicate records"):
        validate_stock_data(df, "AAPL")


def test_zero_closing_price_is_rejected(valid_stock_data):
    df = valid_stock_data.copy()
    df.loc[0, "Close"] = 0

    with pytest.raises(ValueError, match="closing price"):
        validate_stock_data(df, "AAPL")


def test_negative_closing_price_is_rejected(valid_stock_data):
    df = valid_stock_data.copy()
    df.loc[0, "Close"] = -1

    with pytest.raises(ValueError, match="closing price"):
        validate_stock_data(df, "AAPL")


def test_negative_volume_is_rejected(valid_stock_data):
    df = valid_stock_data.copy()
    df.loc[0, "Volume"] = -1

    with pytest.raises(ValueError, match="Invalid volume"):
        validate_stock_data(df, "AAPL")
        