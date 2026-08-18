from datetime import datetime

import joblib
import pandas as pd
from sqlalchemy import text

from database import get_db_engine


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MODEL_PATH = "models/best_model.pkl"

FEATURES = [
    "living_space",
    "rooms",
    "year_built",
    "lot_area",
    "state",
    "region",
    "condition",
    "building_type",
]


# --------------------------------------------------
# Load trained model
# --------------------------------------------------

def load_model():
    print("Loading trained model...")

    model = joblib.load(MODEL_PATH)

    print("Model loaded successfully.")

    return model


# --------------------------------------------------
# Fetch listings that have not been scored yet
# --------------------------------------------------

def load_unscored_listings(engine):

    query = """
        SELECT
            id,
            source_listing_id,
            living_space,
            rooms,
            year_built,
            lot_area,
            state,
            region,
            condition,
            building_type,
            asking_price,
            last_seen_at,
            predicted_at
            
        FROM listings

        WHERE predicted_price IS NULL

        ORDER BY id;
    """

    df = pd.read_sql(
        query,
        engine
    )

    return df


# --------------------------------------------------
# Generate model predictions
# --------------------------------------------------

def generate_predictions(df, model):

    print(f"Scoring {len(df)} new listing(s)...")

    X = df[FEATURES]

    df["predicted_price"] = model.predict(X)

    return df


# --------------------------------------------------
# Calculate valuation metrics
# --------------------------------------------------

def calculate_valuation_metrics(df):

    # Difference between model estimate and asking price
    df["valuation_delta"] = (
        df["predicted_price"]
        - df["asking_price"]
    )

    # Percentage difference relative to asking price
    df["valuation_delta_pct"] = (
        df["valuation_delta"]
        / df["asking_price"]
        * 100
    )

    return df


# --------------------------------------------------
# Save predictions back to PostgreSQL
# --------------------------------------------------

def save_predictions(engine, df):

    update_query = text("""
        UPDATE listings

        SET
            predicted_price = :predicted_price,
            valuation_delta = :valuation_delta,
            valuation_delta_pct = :valuation_delta_pct,
            predicted_at = :predicted_at

        WHERE id = :id;
    """)

    predicted_at = datetime.now()

    with engine.begin() as conn:

        for _, row in df.iterrows():

            conn.execute(
                update_query,
                {
                    "id": int(row["id"]),

                    "predicted_price": float(
                        row["predicted_price"]
                    ),

                    "valuation_delta": float(
                        row["valuation_delta"]
                    ),

                    "valuation_delta_pct": float(
                        row["valuation_delta_pct"]
                    ),

                    "predicted_at": predicted_at,
                }
            )

    print(
        f"Saved predictions for {len(df)} listing(s) "
        "to PostgreSQL."
    )

# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def score_listings():

    print("=" * 60)
    print("NEW LISTING SCORING PIPELINE")
    print("=" * 60)

    # Database connection
    engine = get_db_engine()

    # Load unscored listings
    df = load_unscored_listings(engine)

    if df.empty:
        print("\nNo new listings found to score.")
        return

    print(f"\nFound {len(df)} unscored listing(s).")

    # --------------------------------------------------
    # Load ML model
    # --------------------------------------------------

    model = load_model()

    # --------------------------------------------------
    # Generate predictions
    # --------------------------------------------------

    df = generate_predictions(
        df,
        model
    )

    # --------------------------------------------------
    # Calculate valuation metrics
    # --------------------------------------------------

    df = calculate_valuation_metrics(df)

    # --------------------------------------------------
    # Display prediction preview
    # --------------------------------------------------

    print("\nPrediction preview:")

    display_columns = [
        "id",
        "source_listing_id",
        "state",
        "region",
        "asking_price",
        "predicted_price",
        "valuation_delta",
        "valuation_delta_pct",
    ]

    print(
        df[display_columns].to_string(
            index=False
        )
    )

    # --------------------------------------------------
    # Save predictions to PostgreSQL
    # --------------------------------------------------

    save_predictions(
        engine,
        df
    )

    print("\nSaved predictions successfully.")

    # --------------------------------------------------
    # Reload scored listings from PostgreSQL
    # --------------------------------------------------

    scored_ids = df["id"].tolist()

    placeholders = ", ".join(
        [str(int(x)) for x in scored_ids]
    )

    updated_query = f"""
        SELECT
            id,
            source_listing_id,
            state,
            region,
            asking_price,
            predicted_price,
            valuation_delta,
            valuation_delta_pct,
            last_seen_at,
            predicted_at
        FROM listings
        WHERE id IN ({placeholders})
        ORDER BY id;
    """

    updated_df = pd.read_sql(
        updated_query,
        engine
    )

    # --------------------------------------------------
    # Display updated database records
    # --------------------------------------------------

    print("\nUpdated database records:")

    print(
        updated_df.to_string(
            index=False
        )
    )

    print("\n" + "=" * 60)
    print("SCORING COMPLETE")
    print("=" * 60)


# --------------------------------------------------
# Run script
# --------------------------------------------------

if __name__ == "__main__":
    score_listings()
