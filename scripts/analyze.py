from sqlalchemy import create_engine
import pandas as pd


def analyze_stock_data():
    """
    Run analysis queries on the stock market database.
    """

    print("Analyzing stock market data...")

    engine = create_engine("sqlite:///database/stocks.db")

    query = "SELECT * FROM stocks"

    df = pd.read_sql(query, engine)

    print("\nTotal number of records:")
    print(len(df))

    highest_close = df["Close"].max()

    print("\nHighest closing price:")
    print(highest_close)

    lowest_close = df["Close"].min()

    print("\nLowest closing price:")
    print(lowest_close)

    average_close = df["Close"].mean()

    print("\nAverage closing price:")
    print(average_close)

    average_volume = df["Volume"].mean()

    print("\nAverage trading volume:")
    print(average_volume)

    highest_return = df["Daily_Return"].max()

    print("\nHighest daily return (%):")
    print(highest_return)

    lowest_return = df["Daily_Return"].min()

    print("\nLowest daily return (%):")
    print(lowest_return)

    return df


if __name__ == "__main__":
    analyze_stock_data()
    