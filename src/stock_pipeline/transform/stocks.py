
from datetime import datetime, timezone

import pandas as pd

from stock_pipeline.config import PROCESSED_DATA_DIR, QUARANTINE_DIR
from stock_pipeline.quality.validation import validate_stock_data


REQUIRED_VALUE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]


def _save_quarantined_rows(
    rows: pd.DataFrame,
    ticker: str,
) -> None:
    """Append rejected transformation records to a ticker-specific CSV."""

    if rows.empty:
        return

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    output_file = QUARANTINE_DIR / f"{ticker}_quarantine.csv"

    quarantined = rows.copy()
    quarantined["quarantined_at_utc"] = datetime.now(
        timezone.utc
    ).isoformat()

    if output_file.exists():
        existing = pd.read_csv(output_file)
        quarantined = pd.concat(
            [existing, quarantined],
            ignore_index=True,
        )

    quarantined.to_csv(output_file, index=False)


def transform_stock_data(
    df: pd.DataFrame,
    ticker: str,
) -> pd.DataFrame:
    """Clean, validate, and transform stock data for one ticker."""

    print(f"Transforming data for {ticker}...")

    df = df.copy()

    # Flatten MultiIndex columns.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Make Date a normal column.
    if "Date" not in df.columns:
        df.reset_index(inplace=True)

    # Required columns must exist before row-level cleaning.
    required_columns = [
        "Date",
        *REQUIRED_VALUE_COLUMNS,
    ]
    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{ticker}: Missing columns: {missing_columns}"
        )

    # Standardise the ticker for this dataset.
    df["Ticker"] = ticker

    # Convert dates before identifying invalid rows.
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Identify rows that cannot continue through the transformation.
    invalid_date = df["Date"].isna()

    missing_values = df[REQUIRED_VALUE_COLUMNS].isna().any(axis=1)

    duplicate = df.duplicated(
        subset=["Ticker", "Date"],
        keep="first",
    )

    rejected = invalid_date | missing_values | duplicate

    if rejected.any():
        quarantined = df.loc[rejected].copy()

        quarantined["quarantine_reason"] = [
            (
                "invalid_date"
                if invalid_date.loc[index]
                else "missing_required_value"
                if missing_values.loc[index]
                else "duplicate_ticker_date"
            )
            for index in quarantined.index
        ]

        _save_quarantined_rows(quarantined, ticker)

    # Keep only records that passed these cleaning checks.
    df = df.loc[~rejected].copy()

    # Sort chronologically.
    df.sort_values(
        by=["Ticker", "Date"],
        inplace=True,
    )

    # Validate remaining data before calculating analytics.
    validate_stock_data(df, ticker)

    # Daily percentage return.
    df["Daily_Return"] = (
        df.groupby("Ticker")["Close"]
        .pct_change()
        * 100
    )

    # Five-day moving average.
    df["MA5"] = (
        df.groupby("Ticker")["Close"]
        .transform(lambda prices: prices.rolling(5).mean())
    )

    # Twenty-day moving average.
    df["MA20"] = (
        df.groupby("Ticker")["Close"]
        .transform(lambda prices: prices.rolling(20).mean())
    )

    # Save validated, processed data.
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_DATA_DIR / f"{ticker}_stock_clean.csv"

    df.to_csv(output_file, index=False)

    print(f"Processed data saved to {output_file}")

    return df
