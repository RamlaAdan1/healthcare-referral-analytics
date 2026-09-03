from pathlib import Path

import duckdb
import pandas as pd


BASE_DIR = Path(__file__).parent
RAW_FILE = BASE_DIR / "data" / "referral_kpis.csv"
DATABASE_FILE = BASE_DIR / "data" / "referral_warehouse.duckdb"


def build_data_pipeline():
    # Extract: read the raw CSV data
    data = pd.read_csv(RAW_FILE)

    # Check that all required columns exist
    required_columns = {
        "metric",
        "category",
        "as_is",
        "to_be",
        "unit"
    }

    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")

    # Transform: clean the data
    data = data.drop_duplicates().dropna()

    # Calculate the changes
    data["change"] = (data["to_be"] - data["as_is"]).round(2)

    data["percentage_change"] = (
        (data["change"] / data["as_is"]) * 100
    ).round(2)

    # Load: save the clean data into a SQL database
    with duckdb.connect(str(DATABASE_FILE)) as connection:
        connection.register("referral_dataframe", data)

        connection.execute("""
            CREATE OR REPLACE TABLE referral_kpis AS
            SELECT * FROM referral_dataframe
        """)

    return data


if __name__ == "__main__":
    build_data_pipeline()
