
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

    if df["Date"].isna().any():
        raise ValueError(f"{ticker}: Invalid dates detected")

    if df.duplicated(subset=["Ticker", "Date"]).any():
        duplicates = int(
            df.duplicated(subset=["Ticker", "Date"]).sum()
        )
        raise ValueError(
            f"{ticker}: Found {duplicates} duplicate records"
        )

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

    if (df[PRICE_COLUMNS] <= 0).any().any():
        raise ValueError(f"{ticker}: Invalid price detected (closing price and all other prices must be positive)")

    if (df["Volume"] < 0).any():
        raise ValueError(f"{ticker}: Invalid volume detected")

    if (df["High"] < df["Low"]).any():
        raise ValueError(f"{ticker}: High price cannot be below Low")

    if (
        (df["High"] < df["Open"])
        | (df["High"] < df["Close"])
    ).any():
        raise ValueError(
            f"{ticker}: High price cannot be below Open or Close"
        )

    if (
        (df["Low"] > df["Open"])
        | (df["Low"] > df["Close"])
    ).any():
        raise ValueError(
            f"{ticker}: Low price cannot be above Open or Close"
        )

    return True
