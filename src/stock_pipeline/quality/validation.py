import pandas as pd


REQUIRED_COLUMNS = [
    "Date",
    "Ticker",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume"
]


def validate_stock_data(df: pd.DataFrame, ticker: str) -> bool:
    """
    Validate stock data before loading it.
    """

    print(f"Validating data for {ticker}...")

    # Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{ticker}: Missing columns: {missing_columns}"
        )

    # Check dataframe isn't empty
    if df.empty:
        raise ValueError(
            f"{ticker}: DataFrame is empty"
        )

    # Check duplicate ticker/date combinations
    duplicates = df.duplicated(
        subset=["Ticker", "Date"]
    ).sum()

    if duplicates > 0:
        raise ValueError(
            f"{ticker}: Found {duplicates} duplicate records"
        )

    # Check prices are positive
    if (df["Close"] <= 0).any():
        raise ValueError(
            f"{ticker}: Invalid closing price detected"
        )

    # Check volume
    if (df["Volume"] < 0).any():
        raise ValueError(
            f"{ticker}: Invalid volume detected"
        )

    print(f"Validation passed for {ticker}")

    return True