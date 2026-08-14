import pandas as pd
from sqlalchemy import create_engine


def load_to_postgres(
    df: pd.DataFrame,
    connection_string: str
) -> None:
    """
    Load processed stock data into PostgreSQL.
    """

    print("Loading data into PostgreSQL...")

    engine = create_engine(connection_string)

    df.to_sql(
        name="stocks",
        con=engine,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(
        f"Successfully loaded {len(df)} records."
    )