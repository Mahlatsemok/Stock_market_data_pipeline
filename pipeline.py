import pandas as pd

from scripts.extract import extract_stock_data
from scripts.transform import transform_stock_data
from scripts.load import load_to_database


def main():

    print("=" * 50)
    print("Stock Market Data Pipeline")
    print("=" * 50)

    tickers = [
        "AAPL",
        "MSFT",
        "TSLA",
        "NVDA"
    ]

    processed_data = []

    for ticker in tickers:

        print(f"\nProcessing {ticker}...")

        # Extract
        raw_data = extract_stock_data(ticker)

        # Transform
        transformed_data = transform_stock_data(
            raw_data,
            ticker
        )

        processed_data.append(
            transformed_data
        )

    # Combine all stocks
    print("\nCombining stock data...")

    all_stock_data = pd.concat(
        processed_data,
        ignore_index=True
    )

    # Load into database
    load_to_database(
        all_stock_data
    )

    print("\n" + "=" * 50)
    print("Pipeline completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
