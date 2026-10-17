
import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "Date",
    "Ticker",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]

PRICE_COLUMNS = ["Open", "High", "Low", "Close"]
NUMERIC_COLUMNS = PRICE_COLUMNS + ["Volume"]


def validate_stock_data(df: pd.DataFrame, ticker: str) -> bool:
    """Validate stock market data before downstream processing."""

    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"{ticker}: Input must be a pandas DataFrame")

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{ticker}: Missing columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError(f"{ticker}: DataFrame is empty")

    if df[["Ticker", "Date"]].isna().any().any():
        raise ValueError(f"{ticker}: Ticker and Date cannot be missing")

    if not df["Ticker"].eq(ticker).all():
        raise ValueError(
            f"{ticker}: Data contains mismatched ticker values"
        )

    parsed_dates = pd.to_datetime(df["Date"], errors="coerce")
    if parsed_dates.isna().any():
        raise ValueError(f"{ticker}: Invalid dates detected")

    record_keys = pd.DataFrame(
        {"Ticker": df["Ticker"], "Date": parsed_dates},
        index=df.index,
    )
    if record_keys.duplicated().any():
        duplicates = int(
            record_keys.duplicated().sum()
        )
        raise ValueError(
            f"{ticker}: Found {duplicates} duplicate records"
        )

    numeric_values = {}
    for column in NUMERIC_COLUMNS:
        try:
            values = pd.to_numeric(df[column], errors="raise")
        except (ValueError, TypeError) as error:
            raise ValueError(
                f"{ticker}: Non-numeric values detected in {column}"
            ) from error

        if values.isna().any():
            raise ValueError(
                f"{ticker}: Missing values detected in {column}"
            )

        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(
                f"{ticker}: Non-finite values detected in {column}"
            )

        numeric_values[column] = values

    prices = pd.DataFrame(
        {column: numeric_values[column] for column in PRICE_COLUMNS},
        index=df.index,
    )
    volume = numeric_values["Volume"]

    if (prices <= 0).any().any():
        raise ValueError(f"{ticker}: Invalid price detected (closing price and all other prices must be positive)")

    if (volume < 0).any():
        raise ValueError(f"{ticker}: Invalid volume detected")

    if not np.equal(volume.to_numpy(dtype=float) % 1, 0).all():
        raise ValueError(f"{ticker}: Volume must contain whole numbers")

    if (prices["High"] < prices["Low"]).any():
        raise ValueError(f"{ticker}: High price cannot be below Low")

    if (
        (prices["High"] < prices["Open"])
        | (prices["High"] < prices["Close"])
    ).any():
        raise ValueError(
            f"{ticker}: High price cannot be below Open or Close"
        )

    if (
        (prices["Low"] > prices["Open"])
        | (prices["Low"] > prices["Close"])
    ).any():
        raise ValueError(
            f"{ticker}: Low price cannot be above Open or Close"
        )

    return True
