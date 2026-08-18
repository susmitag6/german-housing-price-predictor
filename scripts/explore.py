import pandas as pd


DATA_PATH = "data/processed/germany_housing.csv"


def explore_data():

    df = pd.read_csv(DATA_PATH)

    print("=" * 60)
    print("GERMAN HOUSING DATASET")
    print("=" * 60)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # -----------------------------------------
    # Price distribution
    # -----------------------------------------

    print("\nPRICE STATISTICS")
    print("-" * 60)

    print(
        df["price"].describe(
            percentiles=[0.01, 0.05, 0.25, 0.50,
                         0.75, 0.95, 0.99]
        )
    )

    # -----------------------------------------
    # Living space
    # -----------------------------------------

    print("\nLIVING SPACE STATISTICS")
    print("-" * 60)

    print(df["living_space"].describe())

    # -----------------------------------------
    # Most common states
    # -----------------------------------------

    print("\nTOP STATES")
    print("-" * 60)

    print(
        df["state"]
        .value_counts()
        .head(20)
    )

    # -----------------------------------------
    # Most common regions
    # -----------------------------------------

    print("\nTOP REGIONS")
    print("-" * 60)

    print(
        df["region"]
        .value_counts()
        .head(20)
    )

    # -----------------------------------------
    # Property conditions
    # -----------------------------------------

    print("\nPROPERTY CONDITIONS")
    print("-" * 60)

    print(
        df["condition"]
        .value_counts(dropna=False)
    )

    # -----------------------------------------
    # Building types
    # -----------------------------------------

    print("\nBUILDING TYPES")
    print("-" * 60)

    print(
        df["building_type"]
        .value_counts(dropna=False)
    )


if __name__ == "__main__":
    explore_data()
