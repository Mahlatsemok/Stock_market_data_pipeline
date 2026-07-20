from scripts.extract import extract_stock_data


def main():
    print("=" * 40)
    print("Stock Market Data Pipeline")
    print("=" * 40)

    data = extract_stock_data()

    print()
    print(data)

    print("\nPipeline completed successfully!")


if __name__ == "__main__":
    main()
