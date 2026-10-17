import logging
import math
import re
import time

import pandas as pd
import yfinance as yf

from stock_pipeline.config import RAW_DATA_DIR
from stock_pipeline.bronze.ingestion import ingest_to_bronze


logger = logging.getLogger(__name__)


def extract_stock_data(
    ticker: str,
    period: str = "10y",
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> pd.DataFrame:
    """
    Extract historical stock data from Yahoo Finance.

    Retries failed requests before returning an empty DataFrame.
    """

    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("ticker must be a non-empty string")

    if not isinstance(period, str) or not period.strip():
        raise ValueError("period must be a non-empty string")

    if (
        isinstance(max_retries, bool)
        or not isinstance(max_retries, int)
        or max_retries < 1
    ):
        raise ValueError("max_retries must be a positive integer")

    if (
        isinstance(retry_delay, bool)
        or not isinstance(retry_delay, (int, float))
        or not math.isfinite(retry_delay)
        or retry_delay < 0
    ):
        raise ValueError(
            "retry_delay must be a finite, non-negative number"
        )

    ticker = ticker.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        raise ValueError("ticker contains unsupported characters")

    period = period.strip()

    logger.info(
        "Starting extraction for ticker=%s, period=%s, "
        "max_retries=%d, retry_delay=%s",
        ticker,
        period,
        max_retries,
        retry_delay,
    )

    for attempt in range(1, max_retries + 1):

        logger.info(
            "Extraction attempt %d/%d for ticker=%s",
            attempt,
            max_retries,
            ticker,
        )

        try:

            stock_data = yf.download(
                ticker,
                period=period,
                auto_adjust=False,
                progress=False,
                threads=False,
                timeout=30,
            )

            if stock_data is None or not isinstance(
                stock_data, pd.DataFrame
            ):

                logger.warning(
                    "Unexpected response for %s "
                    "(attempt %d/%d)",
                    ticker,
                    attempt,
                    max_retries
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue

                return pd.DataFrame()

            if stock_data.empty:
                logger.warning(
                    "No data returned for %s "
                    "(attempt %d/%d)",
                    ticker,
                    attempt,
                    max_retries,
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)
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

            # Validate the minimum expected market-data schema
            required_columns = {
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            }

            missing_columns = (
                required_columns - set(stock_data.columns)
            )

            if missing_columns:
                logger.warning(
                    "Missing expected columns for %s "
                    "(attempt %d/%d): %s",
                    ticker,
                    attempt,
                    max_retries,
                    sorted(missing_columns),
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue

                return pd.DataFrame()

            # Add ticker
            stock_data["Ticker"] = ticker

            # Ensure the raw-data directory exists
            RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

            # Save raw data
            output_file = (
                RAW_DATA_DIR /
                f"{ticker}_stock.csv"
            )

            stock_data.to_csv(
                output_file
            )

            # Bronze ingestion must not invalidate a successful extraction.
            try:
                ingest_to_bronze(
                    stock_data,
                    ticker,
                    source="yahoo_finance",
                )
            except Exception:
                logger.exception(
                    "Bronze ingestion failed for ticker=%s; "
                    "raw data remains saved at %s",
                    ticker,
                    output_file,
                )

            logger.info(
                "Extraction successful for ticker=%s; rows=%d; saved_to=%s",
                ticker,
                len(stock_data),
                output_file,
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
                time.sleep(retry_delay)

    return pd.DataFrame()
