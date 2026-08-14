import pandas as pd

from stock_pipeline.config import PROCESSED_DATA_DIR


def transform_stock_data(
    df: pd.DataFrame,
    ticker: str
) -> pd.DataFrame:
    """
    Clean and transform stock data for one ticker.
    """

    print(f"Transforming data for {ticker}...")

    df = df.copy()

    # Flatten MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Make Date a normal column
    if "Date" not in df.columns:
        df.reset_index(inplace=True)

    # Convert date
    df["Date"] = pd.to_datetime(df["Date"])

    # Ensure ticker exists
    df["Ticker"] = ticker

    # Remove duplicates
    df.drop_duplicates(
        subset=["Ticker", "Date"],
        inplace=True
    )

    # Sort correctly
    df.sort_values(
        by=["Ticker", "Date"],
        inplace=True
    )

    # Remove invalid rows
    df.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ],
        inplace=True
    )

    # Daily return
    df["Daily_Return"] = (
        df.groupby("Ticker")["Close"]
        .pct_change()
        * 100
    )

    # 5-day moving average
    df["MA5"] = (
        df.groupby("Ticker")["Close"]
        .transform(
            lambda x: x.rolling(5).mean()
        )
    )

    # 20-day moving average
    df["MA20"] = (
        df.groupby("Ticker")["Close"]
        .transform(
            lambda x: x.rolling(20).mean()
        )
    )

    # Save processed data
    output_file = (
        PROCESSED_DATA_DIR /
        f"{ticker}_stock_clean.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Processed data saved to {output_file}"
    )

    return df