
from datetime import datetime, timezone
from pathlib import Path
import re

import pandas as pd

from stock_pipeline.config import BRONZE_DATA_DIR


def ingest_to_bronze(
    df: object,
    ticker: str,
    source: str = "yahoo_finance",
) -> Path:
    """Save a traceable, timestamped snapshot of raw stock data."""

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    if df.empty:
        raise ValueError("Cannot ingest an empty DataFrame")

    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("ticker must be a non-empty string")

    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")

    ticker = ticker.strip().upper()
    source = source.strip()

    if not re.fullmatch(r"[A-Z0-9.^_-]+", ticker):
        raise ValueError("ticker contains unsupported characters")

    # Work on a copy so the caller's DataFrame remains unchanged.
    bronze_df = df.copy()

    # Convert a named or unnamed date index into a regular column.
    if "Date" not in bronze_df.columns:
        bronze_df.index.name = "Date"
        bronze_df = bronze_df.reset_index()

    # Preserve an existing ticker column; add it if it is absent.
    if "Ticker" not in bronze_df.columns:
        bronze_df["Ticker"] = ticker

    # Attach ingestion metadata to every row.
    ingested_at = datetime.now(timezone.utc).isoformat()
    bronze_df["ingested_at_utc"] = ingested_at
    bronze_df["source_system"] = source

    BRONZE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    output_file = (
        BRONZE_DATA_DIR / f"{ticker}_{timestamp}.csv"
    )

    bronze_df.to_csv(output_file, index=False)

    return output_file
