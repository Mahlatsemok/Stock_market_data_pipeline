
import pandas as pd

from stock_pipeline.config import PROCESSED_DATA_DIR
from stock_pipeline.quality.validation import validate_stock_data


def transform_stock_data(
    df: pd.DataFrame,
    ticker: str,
) -> pd.DataFrame:
    """Clean, validate, and transform stock data for one ticker."""

    print(f"Transforming data for {ticker}...")

    df = df.copy()

    # Flatten MultiIndex columns.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Make Date a normal column.
    if "Date" not in df.columns:
        df.reset_index(inplace=True)

    # Standardise the ticker for this dataset.
    df["Ticker"] = ticker

    # Convert dates before sorting and validation.
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Remove duplicate ticker/date records.
    df.drop_duplicates(
        subset=["Ticker", "Date"],
        inplace=True,
    )

    # Sort chronologically.
    df.sort_values(
        by=["Ticker", "Date"],
        inplace=True,
    )

    # Remove rows with missing required market values.
    df.dropna(
        subset=[
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ],
        inplace=True,
    )

    # Validate the remaining data before calculating analytics.
    validate_stock_data(df, ticker)

    # Daily percentage return.
    df["Daily_Return"] = (
        df.groupby("Ticker")["Close"]
        .pct_change()
        * 100
    )

    # Five-day moving average.
    df["MA5"] = (
        df.groupby("Ticker")["Close"]
        .transform(lambda prices: prices.rolling(5).mean())
    )

    # Twenty-day moving average.
    df["MA20"] = (
        df.groupby("Ticker")["Close"]
        .transform(lambda prices: prices.rolling(20).mean())
    )

    # Save validated, processed data.
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_DATA_DIR / f"{ticker}_stock_clean.csv"

    df.to_csv(output_file, index=False)

    print(f"Processed data saved to {output_file}")

    return df
