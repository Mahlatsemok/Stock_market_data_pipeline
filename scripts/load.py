import os

from sqlalchemy import create_engine, text


def load_to_database(df):
    """
    Load processed stock market data into a SQLite database.
    """

    print("Loading data into SQLite database...")

    # Create database folder if it doesn't exist
    os.makedirs("database", exist_ok=True)

    # Create SQLite database connection
    engine = create_engine(
        "sqlite:///database/stocks.db"
    )

    # Load the complete dataset into the stocks table
    df.to_sql(
        name="stocks",
        con=engine,
        if_exists="replace",
        index=False
    )

    # Check how many records were loaded
    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT COUNT(*) FROM stocks")
        )

        record_count = result.scalar()

    print(
        f"Successfully loaded {record_count} records "
        "into database/stocks.db"
    )