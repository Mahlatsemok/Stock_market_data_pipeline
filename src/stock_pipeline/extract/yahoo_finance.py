import logging
import time

import pandas as pd
import yfinance as yf

from stock_pipeline.config import RAW_DATA_DIR


logger = logging.getLogger(__name__)


def extract_stock_data(
    ticker: str,
    period: str = "10y",
    max_retries: int = 3
) -> pd.DataFrame:
    """
    Extract historical stock data from Yahoo Finance.

    Retries failed requests before returning an empty DataFrame.
    """

    logger.info(
        "Downloading data for %s...",
        ticker
    )

    for attempt in range(1, max_retries + 1):

        try:

            stock_data = yf.download(
                ticker,
                period=period,
                auto_adjust=False,
                progress=True
            )

            if stock_data.empty:

                logger.warning(
                    "No data returned for %s "
                    "(attempt %d/%d)",
                    ticker,
                    attempt,
                    max_retries
                )

                if attempt < max_retries:
                    time.sleep(2)
                    continue

                return pd.DataFrame()

            # Flatten MultiIndex columns
            if isinstance(
                stock_data.columns,
                pd.MultiIndex
            ):
                stock_data.columns = (
                    stock_data.columns
                    .get_level_values(0)
                )

            # Add ticker
            stock_data["Ticker"] = ticker

            # Save raw data
            output_file = (
                RAW_DATA_DIR /
                f"{ticker}_stock.csv"
            )

            stock_data.to_csv(
                output_file
            )

            logger.info(
                "Raw data saved to %s",
                output_file
            )

            return stock_data

        except Exception as error:

            logger.error(
                "Failed to download %s "
                "(attempt %d/%d): %s",
                ticker,
                attempt,
                max_retries,
                error
            )

            if attempt < max_retries:
                time.sleep(2)

    return pd.DataFrame()