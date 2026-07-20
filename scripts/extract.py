import os

import yfinance as yf


def extract_stock_data():
    """
    Download one year of Apple stock data and save it as a CSV.
    """

    print("Downloading stock market data...")

    # Download one year of Apple stock data
    stock_data = yf.download("AAPL", period="1y")

    # Create the folder if it doesn't exist
    os.makedirs("data/raw", exist_ok=True)

    # Save the data
    file_path = "data/raw/apple_stock.csv"
    stock_data.to_csv(file_path)

    print(f"Data saved to {file_path}")

    return stock_data
