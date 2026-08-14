import pandas as pd


def calculate_stock_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate summary metrics for each stock.
    """

    metrics = (
        df.groupby("Ticker")
        .agg(
            total_records=("Date", "count"),
            highest_close=("Close", "max"),
            lowest_close=("Close", "min"),
            average_close=("Close", "mean"),
            average_volume=("Volume", "mean"),
            best_daily_return=("Daily_Return", "max"),
            worst_daily_return=("Daily_Return", "min"),
            average_daily_return=("Daily_Return", "mean"),
            volatility=("Daily_Return", "std")
        )
        .reset_index()
    )

    return metrics