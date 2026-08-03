from sqlalchemy import create_engine
import pandas as pd


def analyze_stock_data():
    """
    Analyze stock market data stored in the SQLite database.
    """

    print("=" * 60)
    print("STOCK MARKET DATA ANALYSIS")
    print("=" * 60)

    # Connect to database
    engine = create_engine(
        "sqlite:///database/stocks.db"
    )

    # Load stock data from database
    query = """
        SELECT *
        FROM stocks
    """

    df = pd.read_sql(
        query,
        engine
    )

    # ------------------------------------------------
    # Total records
    # ------------------------------------------------

    print("\nTotal records per stock:")

    record_counts = (
        df.groupby("Ticker")
        .size()
        .sort_values(ascending=False)
    )

    print(record_counts)

    # ------------------------------------------------
    # Highest closing price
    # ------------------------------------------------

    print("\nHighest closing price per stock:")

    highest_close = (
        df.groupby("Ticker")["Close"]
        .max()
        .sort_values(ascending=False)
    )

    print(highest_close)

    # ------------------------------------------------
    # Lowest closing price
    # ------------------------------------------------

    print("\nLowest closing price per stock:")

    lowest_close = (
        df.groupby("Ticker")["Close"]
        .min()
        .sort_values()
    )

    print(lowest_close)

    # ------------------------------------------------
    # Average closing price
    # ------------------------------------------------

    print("\nAverage closing price per stock:")

    average_close = (
        df.groupby("Ticker")["Close"]
        .mean()
        .sort_values(ascending=False)
    )

    print(average_close)

    # ------------------------------------------------
    # Average trading volume
    # ------------------------------------------------

    print("\nAverage trading volume per stock:")

    average_volume = (
        df.groupby("Ticker")["Volume"]
        .mean()
        .sort_values(ascending=False)
    )

    print(average_volume)

    # ------------------------------------------------
    # Best daily return
    # ------------------------------------------------

    print("\nBest daily return per stock (%):")

    best_return = (
        df.groupby("Ticker")["Daily_Return"]
        .max()
        .sort_values(ascending=False)
    )

    print(best_return)

    # ------------------------------------------------
    # Worst daily return
    # ------------------------------------------------

    print("\nWorst daily return per stock (%):")

    worst_return = (
        df.groupby("Ticker")["Daily_Return"]
        .min()
        .sort_values()
    )

    print(worst_return)

    # ------------------------------------------------
    # Average daily return
    # ------------------------------------------------

    print("\nAverage daily return per stock (%):")

    average_return = (
        df.groupby("Ticker")["Daily_Return"]
        .mean()
        .sort_values(ascending=False)
    )

    print(average_return)

    # ------------------------------------------------
    # Volatility
    # ------------------------------------------------

    print("\nDaily return volatility per stock (%):")

    volatility = (
        df.groupby("Ticker")["Daily_Return"]
        .std()
        .sort_values(ascending=False)
    )

    print(volatility)

    # ------------------------------------------------
    # Best performing stock
    # ------------------------------------------------

    best_stock = average_return.idxmax()

    print("\nBest performing stock based on average daily return:")

    print(best_stock)

    # ------------------------------------------------
    # Most volatile stock
    # ------------------------------------------------

    most_volatile_stock = volatility.idxmax()

    print(
        "\nMost volatile stock:"
    )

    print(most_volatile_stock)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    analyze_stock_data()