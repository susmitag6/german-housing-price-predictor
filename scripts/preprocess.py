import os
import pandas as pd


RAW_DATA_PATH = "data/raw/apr20_price.csv"
PROCESSED_DATA_PATH = "data/processed/germany_housing.csv"


# Columns we want from the original dataset
COLUMNS_TO_USE = [
    "obj_purchasePrice",
    "obj_livingSpace",
    "obj_noRooms",
    "obj_yearConstructed",
    "obj_lotArea",
    "obj_regio1",
    "obj_regio2",
    "obj_condition",
    "obj_buildingType",
    "obj_heatingType",
    "obj_cellar",
    "obj_noParkSpaces",
    "obj_newlyConst",
]


# Rename ugly source column names to simple names
COLUMN_NAMES = {
    "obj_purchasePrice": "price",
    "obj_livingSpace": "living_space",
    "obj_noRooms": "rooms",
    "obj_yearConstructed": "year_built",
    "obj_lotArea": "lot_area",
    "obj_regio1": "state",
    "obj_regio2": "region",
    "obj_condition": "condition",
    "obj_buildingType": "building_type",
    "obj_heatingType": "heating_type",
    "obj_cellar": "cellar",
    "obj_noParkSpaces": "parking_spaces",
    "obj_newlyConst": "newly_constructed",
}


def preprocess_data():

    print("Loading German housing data...")

    # Only load columns we actually need
    df = pd.read_csv(
        RAW_DATA_PATH,
        usecols=COLUMNS_TO_USE
    )

    print(f"Original rows: {len(df):,}")

    # Rename columns
    df = df.rename(columns=COLUMN_NAMES)

    print("\nSelected columns:")
    print(df.columns.tolist())

    # --------------------------------------------------
    # 1. Remove rows where target is missing
    # --------------------------------------------------

    df = df.dropna(subset=["price"])

    # --------------------------------------------------
    # 2. Remove duplicates
    # --------------------------------------------------

    before = len(df)
    df = df.drop_duplicates()

    print(f"Duplicates removed: {before - len(df):,}")

    # --------------------------------------------------
    # 3. Basic sanity filters
    # --------------------------------------------------

    # Property price must be positive
#    df = df[df["price"] > 0]
    # Keep realistic residential purchase prices
    df = df[
        (df["price"] >= 50_000) &
        (df["price"] <= 5_000_000)
]
    # Living space should be realistic
    df = df[
        (df["living_space"].isna()) |
        ((df["living_space"] >= 10) &
         (df["living_space"] <= 1000))
    ]

    # Rooms should be realistic
    df = df[
        (df["rooms"].isna()) |
        ((df["rooms"] >= 1) &
         (df["rooms"] <= 30))
    ]

    # Construction year sanity check
    df = df[
        (df["year_built"].isna()) |
        ((df["year_built"] >= 1800) &
         (df["year_built"] <= 2026))
    ]

    # --------------------------------------------------
    # 4. Save cleaned dataset
    # --------------------------------------------------

    os.makedirs("data/processed", exist_ok=True)

    df.to_csv(
        PROCESSED_DATA_PATH,
        index=False
    )

    print("\n--------------------------------")
    print("PREPROCESSING COMPLETE")
    print("--------------------------------")

    print(f"Final rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nMissing values:")
    print(
        df.isnull()
        .sum()
        .sort_values(ascending=False)
    )

    print("\nPrice statistics:")
    print(df["price"].describe())

    print(
        f"\nSaved cleaned data to:"
        f" {PROCESSED_DATA_PATH}"
    )


if __name__ == "__main__":
    preprocess_data()
