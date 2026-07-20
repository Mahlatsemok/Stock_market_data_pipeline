from scripts.extract import extract_stock_data


def main():
    print("=" * 40)
    print("Stock Market Data Pipeline")
    print("=" * 40)

    extract_stock_data()

    print("Pipeline completed.")


if __name__ == "__main__":
    main()
    