import os

from sqlalchemy import create_engine


def load_to_database(df):
    """
    Load processed stock market data into a SQLite database.
    """

    print("Loading data into SQLite database...")

    # Create the database folder if it doesn't exist
    os.makedirs("database", exist_ok=True)

    # Create a connection to the SQLite database
    engine = create_engine("sqlite:///database/stocks.db")

    # Save the DataFrame to a table called 'stocks'
    df.to_sql(
        name="stocks",
        con=engine,
        if_exists="replace",
        index=False
    )

    print("Data successfully loaded into database/stocks.db")