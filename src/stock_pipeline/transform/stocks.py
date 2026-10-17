from datetime import datetime, timezone

import numpy as np
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

    df["Ticker"] = ticker
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Identify invalid dates and missing values first.
    invalid_date = df["Date"].isna().to_numpy()
    missing_values = (
        df[REQUIRED_VALUE_COLUMNS].isna().any(axis=1).to_numpy()
    )

    # Convert numeric fields without silently accepting bad values.
    numeric_values = pd.DataFrame(index=range(len(df)))

    for column in REQUIRED_VALUE_COLUMNS:
        numeric_values[column] = pd.to_numeric(
            df[column].reset_index(drop=True),
            errors="coerce",
        )

    numeric_array = numeric_values.to_numpy(dtype=float)
    non_numeric_or_non_finite = ~np.isfinite(numeric_array).all(axis=1)

    prices = numeric_values[["Open", "High", "Low", "Close"]]
    volume = numeric_values["Volume"]

    invalid_price = (prices <= 0).any(axis=1).to_numpy()
    invalid_volume = (volume < 0).to_numpy()

    high = numeric_values["High"]
    low = numeric_values["Low"]
    open_price = numeric_values["Open"]
    close = numeric_values["Close"]

    invalid_ohlc = (
        (high < low)
        | (high < open_price)
        | (high < close)
        | (low > open_price)
        | (low > close)
    ).to_numpy()

    # Deduplicate only among otherwise valid records. This keeps a valid
    # observation when an earlier row for the same date is malformed.
    otherwise_valid = ~(
        invalid_date
        | missing_values
        | non_numeric_or_non_finite
        | invalid_price
        | invalid_volume
        | invalid_ohlc
    )
    duplicate = np.zeros(len(df), dtype=bool)
    valid_positions = np.flatnonzero(otherwise_valid)
    duplicate[valid_positions] = df.iloc[valid_positions].duplicated(
        subset=["Ticker", "Date"],
        keep="first",
    ).to_numpy()

    # Give each rejected row one clear, deterministic reason.
    reason_masks = [
        ("invalid_date", invalid_date),
        ("missing_required_value", missing_values),
        ("duplicate_ticker_date", duplicate),
        (
            "non_numeric_or_non_finite_value",
            non_numeric_or_non_finite,
        ),
        ("invalid_price", invalid_price),
        ("invalid_volume", invalid_volume),
        ("inconsistent_ohlc_values", invalid_ohlc),
    ]

    rejected_positions = np.zeros(len(df), dtype=bool)
    reasons = np.full(len(df), "", dtype=object)

    for reason, mask in reason_masks:
        newly_rejected = mask & ~rejected_positions
        reasons[newly_rejected] = reason
        rejected_positions |= mask

    if rejected_positions.any():
        rejected_row_positions = np.flatnonzero(rejected_positions)
        quarantined = df.iloc[rejected_row_positions].copy()
        quarantined["quarantine_reason"] = reasons[
            rejected_row_positions
        ]

        _save_quarantined_rows(quarantined, ticker)

    # Continue only with records that passed row-level checks.
    df = df.iloc[~rejected_positions].copy()

    if df.empty:
        rejected_count = int(rejected_positions.sum())
        raise ValueError(
            f"{ticker}: No valid stock records remain after quarantine; "
            f"{rejected_count} rows were rejected"
        )

    # Use validated numeric representations downstream.
    for column in REQUIRED_VALUE_COLUMNS:
        df[column] = numeric_values.loc[
            ~rejected_positions, column
        ].to_numpy()

    df.sort_values(
        by=["Ticker", "Date"],
        inplace=True,
    )

    # Retain strict dataset-level validation.
    validate_stock_data(df, ticker)

    df["Daily_Return"] = (
        df.groupby("Ticker")["Close"].pct_change() * 100
    )

    df["MA5"] = (
        df.groupby("Ticker")["Close"]
        .transform(lambda prices: prices.rolling(5).mean())
    )

    df["MA20"] = (
        df.groupby("Ticker")["Close"]
        .transform(lambda prices: prices.rolling(20).mean())
    )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_DATA_DIR / f"{ticker}_stock_clean.csv"
    df.to_csv(output_file, index=False)

    print(f"Processed data saved to {output_file}")

    return df
