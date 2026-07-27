from scripts.extract import extract_stock_data
from scripts.transform import transform_stock_data
from scripts.load import load_to_database


def main():
    print("=" * 40)
    print("Stock Market Data Pipeline")
    print("=" * 40)

    # Extract
    raw_data = extract_stock_data()

    print()

    # Transform
    processed_data = transform_stock_data(raw_data)

    # Load
    load_to_database(processed_data)

    #print("\nFirst 5 rows of transformed data:\n")
    print(processed_data)

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    main() 
