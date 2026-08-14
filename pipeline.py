import pandas as pd

from stock_pipeline.extract.yahoo_finance import (
    extract_stock_data
)

from stock_pipeline.transform.stocks import (
    transform_stock_data
)

from stock_pipeline.quality.validation import (
    validate_stock_data
)


TICKERS = [
    "AAPL",
    "MSFT",
    "TSLA",
    "NVDA"
]


def main():

    print("=" * 60)
    print("STOCK MARKET DATA PIPELINE")
    print("=" * 60)

    processed_data = []

    for ticker in TICKERS:

        print(f"\nProcessing {ticker}...")

        # -----------------------------
        # Extract
        # -----------------------------

        raw_data = extract_stock_data(
            ticker,
            period="10y"
        )

        # -----------------------------
        # Transform
        # -----------------------------

        transformed_data = transform_stock_data(
            raw_data,
            ticker
        )

        # -----------------------------
        # Validate
        # -----------------------------

        validate_stock_data(
            transformed_data,
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

    print(
        f"Total records: {len(all_stock_data):,}"
    )

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    main()