import logging

import pandas as pd

from stock_pipeline.config import (
    load_tickers,
    FAILED_TICKERS_FILE,
    COMBINED_DATA_DIR
)

from stock_pipeline.extract.yahoo_finance import (
    extract_stock_data
)

from stock_pipeline.transform.stocks import (
    transform_stock_data
)

from stock_pipeline.quality.validation import (
    validate_stock_data
)

from stock_pipeline.logging_config import (
    setup_logging
)


logger = logging.getLogger(__name__)


def main():

    setup_logging()

    logger.info("=" * 60)
    logger.info("STOCK MARKET DATA PIPELINE")
    logger.info("=" * 60)

    # Load 100 tickers
    tickers = load_tickers()

    logger.info(
        "Stocks configured: %d",
        len(tickers)
    )

    processed_data = []

    failed_tickers = []

    # ========================================================
    # PROCESS EACH STOCK
    # ========================================================

    for ticker in tickers:

        logger.info(
            "Processing %s...",
            ticker
        )

        # ----------------------------------------------------
        # Extract
        # ----------------------------------------------------

        raw_data = extract_stock_data(
            ticker,
            period="10y"
        )

        # ----------------------------------------------------
        # Handle extraction failure
        # ----------------------------------------------------

        if raw_data.empty:

            logger.warning(
                "Skipping %s because extraction failed.",
                ticker
            )

            failed_tickers.append(
                {
                    "Ticker": ticker,
                    "Reason": "No data returned"
                }
            )

            continue

        # ----------------------------------------------------
        # Transform
        # ----------------------------------------------------

        try:

            transformed_data = (
                transform_stock_data(
                    raw_data,
                    ticker
                )
            )

        except Exception as error:

            logger.error(
                "Transformation failed for %s: %s",
                ticker,
                error
            )

            failed_tickers.append(
                {
                    "Ticker": ticker,
                    "Reason": (
                        f"Transformation failed: {error}"
                    )
                }
            )

            continue

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        try:

            validate_stock_data(
                transformed_data,
                ticker
            )

        except Exception as error:

            logger.error(
                "Validation failed for %s: %s",
                ticker,
                error
            )

            failed_tickers.append(
                {
                    "Ticker": ticker,
                    "Reason": (
                        f"Validation failed: {error}"
                    )
                }
            )

            continue

        # ----------------------------------------------------
        # Store successful result
        # ----------------------------------------------------

        processed_data.append(
            transformed_data
        )

    # ========================================================
    # COMBINE DATA
    # ========================================================

    logger.info(
        "Combining stock data..."
    )

    if not processed_data:

        logger.error(
            "No stocks were successfully processed."
        )

        return

    all_stock_data = pd.concat(
        processed_data,
        ignore_index=True
    )

    combined_file = (
    COMBINED_DATA_DIR / "all_stocks_clean.csv"
    )

    all_stock_data.to_csv(
        combined_file,
        index=False
    )

    logger.info(
        "Combined data saved to %s",
        combined_file
    )

    logger.info(
        "Total records: %s",
        f"{len(all_stock_data):,}"
    )

    # ========================================================
    # SAVE FAILED TICKERS
    # ========================================================

    if failed_tickers:

        failed_df = pd.DataFrame(
            failed_tickers
        )

        failed_df.to_csv(
            FAILED_TICKERS_FILE,
            index=False
        )

        logger.warning(
            "%d stocks failed.",
            len(failed_tickers)
        )

        logger.warning(
            "Failed ticker report saved to %s",
            FAILED_TICKERS_FILE
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    successful_count = (
        len(processed_data)
    )

    failed_count = (
        len(failed_tickers)
    )

    logger.info("=" * 60)

    logger.info(
        "PIPELINE SUMMARY"
    )

    logger.info(
        "Configured stocks: %d",
        len(tickers)
    )

    logger.info(
        "Successful stocks: %d",
        successful_count
    )

    logger.info(
        "Failed stocks: %d",
        failed_count
    )

    logger.info(
        "Total records: %s",
        f"{len(all_stock_data):,}"
    )

    logger.info(
        "Pipeline completed."
    )

    logger.info("=" * 60)


if __name__ == "__main__":
    main()