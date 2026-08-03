import os

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine


def load_stock_data():
    """
    Load stock data from the SQLite database.
    """

    engine = create_engine(
        "sqlite:///database/stocks.db"
    )

    query = """
        SELECT *
        FROM stocks
    """

    df = pd.read_sql(
        query,
        engine
    )

    # Convert Date to datetime
    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    return df


def create_output_folder():
    """
    Create the visualizations folder.
    """

    os.makedirs(
        "visualizations",
        exist_ok=True
    )


def plot_closing_prices(df):
    """
    Create a line chart showing closing prices
    for all stocks.
    """

    plt.figure(
        figsize=(12, 6)
    )

    for ticker in df["Ticker"].unique():

        stock_data = df[
            df["Ticker"] == ticker
        ]

        plt.plot(
            stock_data["Date"],
            stock_data["Close"],
            label=ticker
        )

    plt.title(
        "Stock Closing Prices - Last 1 Year"
    )

    plt.xlabel(
        "Date"
    )

    plt.ylabel(
        "Closing Price (USD)"
    )

    plt.legend()

    plt.grid(
        True
    )

    plt.tight_layout()

    plt.savefig(
        "visualizations/closing_prices.png"
    )

    plt.show()

    plt.close()


def plot_average_returns(df):
    """
    Create a bar chart showing average
    daily returns for each stock.
    """

    average_returns = (
        df.groupby("Ticker")["Daily_Return"]
        .mean()
        .sort_values(ascending=False)
    )

    plt.figure(
        figsize=(10, 6)
    )

    average_returns.plot(
        kind="bar"
    )

    plt.title(
        "Average Daily Return by Stock"
    )

    plt.xlabel(
        "Stock"
    )

    plt.ylabel(
        "Average Daily Return (%)"
    )

    plt.xticks(
        rotation=0
    )

    plt.grid(
        axis="y"
    )

    plt.tight_layout()

    plt.savefig(
        "visualizations/average_daily_returns.png"
    )

    plt.show()

    plt.close()


def plot_volatility(df):
    """
    Create a bar chart showing stock volatility.
    """

    volatility = (
        df.groupby("Ticker")["Daily_Return"]
        .std()
        .sort_values(ascending=False)
    )

    plt.figure(
        figsize=(10, 6)
    )

    volatility.plot(
        kind="bar"
    )

    plt.title(
        "Stock Volatility"
    )

    plt.xlabel(
        "Stock"
    )

    plt.ylabel(
        "Daily Return Standard Deviation (%)"
    )

    plt.xticks(
        rotation=0
    )

    plt.grid(
        axis="y"
    )

    plt.tight_layout()

    plt.savefig(
        "visualizations/volatility.png"
    )

    plt.show()

    plt.close()


def plot_average_volume(df):
    """
    Create a bar chart showing average
    trading volume.
    """

    average_volume = (
        df.groupby("Ticker")["Volume"]
        .mean()
        .sort_values(ascending=False)
    )

    plt.figure(
        figsize=(10, 6)
    )

    average_volume.plot(
        kind="bar"
    )

    plt.title(
        "Average Trading Volume by Stock"
    )

    plt.xlabel(
        "Stock"
    )

    plt.ylabel(
        "Average Trading Volume"
    )

    plt.xticks(
        rotation=0
    )

    plt.grid(
        axis="y"
    )

    plt.tight_layout()

    plt.savefig(
        "visualizations/average_volume.png"
    )

    plt.show()

    plt.close()


def main():

    print("=" * 60)
    print("STOCK MARKET DATA VISUALIZATION")
    print("=" * 60)

    # Load data
    print("\nLoading stock data...")

    df = load_stock_data()

    print(
        f"Loaded {len(df)} records."
    )

    # Create output folder
    create_output_folder()

    # Create visualizations
    print(
        "\nCreating closing price chart..."
    )

    plot_closing_prices(df)

    print(
        "Creating average return chart..."
    )

    plot_average_returns(df)

    print(
        "Creating volatility chart..."
    )

    plot_volatility(df)

    print(
        "Creating trading volume chart..."
    )

    plot_average_volume(df)

    print("\nAll visualizations created successfully!")

    print(
        "Check the 'visualizations' folder."
    )


if __name__ == "__main__":
    main()