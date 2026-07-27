import os
import pandas as pd


def transform_stock_data(df):
    """
    Clean and transform stock market data.
    """

    print("Transforming stock market data...")

    # Make a copy so we don't modify the original
    df = df.copy()

    # -----------------------------
    # Flatten MultiIndex columns if needed
    # -----------------------------
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # -----------------------------
    # Remove duplicates
    # -----------------------------
    df.drop_duplicates(inplace=True)

    # -----------------------------
    # Remove missing values
    # -----------------------------
    df.dropna(inplace=True)

    # -----------------------------
    # Convert Date column
    # -----------------------------
    df.reset_index(inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])

    # -----------------------------
    # Sort by Date
    # -----------------------------
    df.sort_values("Date", inplace=True)

    # -----------------------------
    # Daily Return (%)
    # -----------------------------
    df["Daily_Return"] = df["Close"].pct_change() * 100

    # -----------------------------
    # 5-Day Moving Average
    # -----------------------------
    df["MA5"] = df["Close"].rolling(window=5).mean()

    # -----------------------------
    # 20-Day Moving Average
    # -----------------------------
    df["MA20"] = df["Close"].rolling(window=20).mean()

    # -----------------------------
    # Create folder
    # -----------------------------
    os.makedirs("data/processed", exist_ok=True)

    # -----------------------------
    # Save cleaned data
    # -----------------------------
    output_file = "data/processed/apple_stock_clean.csv"
    df.to_csv(output_file, index=False)

    print(f"Processed data saved to {output_file}")

    return df
