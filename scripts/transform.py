import os

import pandas as pd


def transform_stock_data(df, ticker):
    """
    Clean and transform stock market data for a specific ticker.
    """

    print(f"Transforming data for {ticker}...")

    # Make a copy so we don't modify the original DataFrame
    df = df.copy()

    # Flatten MultiIndex columns if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Reset index so Date becomes a normal column
    df.reset_index(inplace=True)

    # Convert Date to datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # Add ticker to identify the stock
    df["Ticker"] = ticker

    # Remove duplicate rows
    df.drop_duplicates(inplace=True)

    # Sort by ticker and date
    df.sort_values(
        by=["Ticker", "Date"],
        inplace=True
    )

    # Remove rows with missing important values
    df.dropna(
        subset=["Open", "High", "Low", "Close", "Volume"],
        inplace=True
    )

    # ------------------------------------------------
    # Group calculations by ticker
    # ------------------------------------------------

    # Calculate Daily Return separately for each stock
    df["Daily_Return"] = (
        df.groupby("Ticker")["Close"]
        .pct_change() * 100
    )

    # Calculate 5-day moving average separately for each stock
    df["MA5"] = (
        df.groupby("Ticker")["Close"]
        .transform(
            lambda x: x.rolling(window=5).mean()
        )
    )

    # Calculate 20-day moving average separately for each stock
    df["MA20"] = (
        df.groupby("Ticker")["Close"]
        .transform(
            lambda x: x.rolling(window=20).mean()
        )
    )

    # Create processed data folder
    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    # Save processed data
    output_file = (
        f"data/processed/{ticker}_stock_clean.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Processed data saved to {output_file}"
    )

    return df