import yfinance as yf
import pandas as pd

from stock_pipeline.config import RAW_DATA_DIR


def extract_stock_data(ticker: str, period: str = "10y") -> pd.DataFrame:
    """
    Extract historical stock data from Yahoo Finance.
    """

    print(f"Downloading data for {ticker}...")

    stock_data = yf.download(
        ticker,
        period=period,
        auto_adjust=False,
        progress=True
    )

    if stock_data.empty:
        raise ValueError(
            f"No data returned from Yahoo Finance for {ticker}"
        )

    # Flatten MultiIndex columns if Yahoo Finance returns them
    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = stock_data.columns.get_level_values(0)

    # Add ticker
    stock_data["Ticker"] = ticker

    # Save raw data
    output_file = RAW_DATA_DIR / f"{ticker}_stock.csv"

    stock_data.to_csv(output_file)

    print(f"Raw data saved to {output_file}")

    return stock_data
