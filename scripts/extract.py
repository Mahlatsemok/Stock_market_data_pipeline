import os

import yfinance as yf


def extract_stock_data(ticker):
    """
    Download one year of stock market data for a given ticker.
    """

    print(f"Downloading data for {ticker}...")

    stock_data = yf.download(
        ticker,
        period="1y",
        auto_adjust=False
    )

    # Add the stock ticker to the data
    stock_data["Ticker"] = ticker

    # Create raw data folder
    os.makedirs("data/raw", exist_ok=True)

    # Save raw data
    file_path = f"data/raw/{ticker}_stock.csv"
    stock_data.to_csv(file_path)

    print(f"Data saved to {file_path}")

    return stock_data
