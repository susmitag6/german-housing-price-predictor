import joblib
import pandas as pd
import streamlit as st

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

MODEL_PATH = "models/best_model.pkl"
DATA_PATH = "data/processed/germany_housing.csv"
RESULTS_PATH = "models/model_results.csv"


# -----------------------------------------
# Load model and data
# -----------------------------------------

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_data():
    @st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error(f"Data file not found at: {DATA_PATH}")
        st.stop()

    return pd.read_csv(DATA_PATH)


model = load_model()
df = load_data()

#@st.cache_data
def load_model_results():
    return pd.read_csv(RESULTS_PATH)


results = load_model_results()

# -----------------------------------------
# Page setup
# -----------------------------------------

st.set_page_config(
    page_title="German House Price Predictor",
    page_icon="🏠",
    layout="centered"
)

st.title("🏠 German House Price Predictor")

st.write(
    "Enter the property details below to get an estimated purchase price."
)



# -----------------------------------------
# Prediction
# -----------------------------------------
# -----------------------------------------
# Location selection
# -----------------------------------------

st.subheader("Location")

col1, col2 = st.columns(2)

with col1:
    states = sorted(
        df["state"]
        .dropna()
        .unique()
    )

    selected_state = st.selectbox(
        "State",
        states,
        key="prediction_state"
    )

with col2:
    regions = sorted(
        df.loc[
            df["state"] == selected_state,
            "region"
        ]
        .dropna()
        .unique()
    )

    if regions:
        selected_region = st.selectbox(
            "Region",
            regions,
            key="prediction_region"
        )
    else:
        selected_region = None
        st.warning(
            "No region information is available for this state."
        )

#------------------------------------------
# -----------------------------------------
# Property details form
# -----------------------------------------

st.subheader("Property Details")

with st.form("prediction_form"):

    col1, col2 = st.columns(2)

    with col1:
        living_space = st.number_input(
            "Living space (m²)",
            min_value=10.0,
            max_value=1000.0,
            value=120.0,
            step=5.0
        )

    with col2:
        rooms = st.number_input(
            "Number of rooms",
            min_value=1.0,
            max_value=30.0,
            value=4.0,
            step=0.5
        )

    col1, col2 = st.columns(2)

    with col1:
        year_built = st.number_input(
            "Year built",
            min_value=1800,
            max_value=2026,
            value=2000,
            step=1
        )

    with col2:
        lot_area = st.number_input(
            "Lot area (m²)",
            min_value=0.0,
            max_value=10000.0,
            value=400.0,
            step=25.0
        )

    col1, col2 = st.columns(2)

    with col1:
        selected_condition = st.selectbox(
            "Property condition",
            sorted(df["condition"].dropna().unique())
        )

    with col2:
        selected_building_type = st.selectbox(
            "Building type",
            sorted(df["building_type"].dropna().unique())
        )

    predict_button = st.form_submit_button(
        "Predict Price",
        use_container_width=True
    )
#-------------------------------------------------------------    
#if st.button("Predict Price", use_container_width=True):
if predict_button:

    property_data = pd.DataFrame([
        {
            "living_space": living_space,
            "rooms": rooms,
            "year_built": year_built,
            "lot_area": lot_area,
            "state": selected_state,
            "region": selected_region,
            "condition": selected_condition,
            "building_type": selected_building_type,
        }
    ])

    prediction = model.predict(property_data)[0]

    price_per_sqm = prediction / living_space

    st.subheader("Prediction Result")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Estimated Purchase Price",
            f"€{prediction:,.0f}"
        )

    with col2:
        st.metric(
            "Estimated Price / m²",
            f"€{price_per_sqm:,.0f}"
        )
    
#----------------------------------------------------------------------------------------    
st.divider()

st.subheader("Model Performance")

st.write(
    "Six regression approaches were evaluated on the same held-out test set."
)

display_results = results.copy()

display_results["MAE"] = display_results["MAE"].map(
    lambda x: f"€{x:,.0f}"
)

display_results["RMSE"] = display_results["RMSE"].map(
    lambda x: f"€{x:,.0f}"
)

display_results["R2"] = display_results["R2"].map(
    lambda x: f"{x:.3f}"
)

chart_data = results[
    ["Model", "R2"]
].set_index("Model")

st.subheader("R² Comparison")

st.bar_chart(chart_data)
st.dataframe(
    display_results,
    use_container_width=True,
    hide_index=True
)

# -----------------------------------------
# Load scored listings from PostgreSQL
# -----------------------------------------

@st.cache_data(ttl=60)
def load_scored_listings():

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")

    engine = create_engine(
        f"postgresql+psycopg2://"
        f"{user}:{password}@{host}:{port}/{database}"
    )

    query = """
        SELECT
            source_listing_id,
            state,
            region,
            living_space,
            rooms,
            year_built,
            asking_price,
            predicted_price,
            valuation_delta,
            valuation_delta_pct,
            last_seen_at
        FROM listings
        WHERE predicted_price IS NOT NULL
        ORDER BY last_seen_at DESC;
    """

    return pd.read_sql(query, engine)
    
# -----------------------------------------
# Latest scored listings
# -----------------------------------------

st.divider()

st.subheader("Latest Scored Listings")

listings_df = load_scored_listings()

if listings_df.empty:

    st.info("No scored listings are available yet.")

else:

    display_df = listings_df.copy()

    display_df["asking_price"] = display_df[
        "asking_price"
    ].map(lambda x: f"€{x:,.0f}")

    display_df["predicted_price"] = display_df[
        "predicted_price"
    ].map(lambda x: f"€{x:,.0f}")

    display_df["valuation_delta"] = display_df[
        "valuation_delta"
    ].map(lambda x: f"€{x:,.0f}")

    display_df["valuation_delta_pct"] = display_df[
        "valuation_delta_pct"
    ].map(lambda x: f"{x:.1f}%")

    display_df = display_df.rename(
        columns={
            "source_listing_id": "Listing ID",
            "state": "State",
            "region": "Region",
            "living_space": "Living Space (m²)",
            "rooms": "Rooms",
            "year_built": "Year Built",
            "asking_price": "Asking Price",
            "predicted_price": "Model Estimate",
            "valuation_delta": "Difference",
            "valuation_delta_pct": "Difference %",
            "last_seen_at": "Last Seen",
        }
    )
    
    
    
# -----------------------------------------
# Listing filters
# -----------------------------------------

st.subheader("Listing Filters")

filter_col1, filter_col2 = st.columns(2)


# -----------------------------------------
# State filter
# -----------------------------------------

with filter_col1:

    listing_states = ["All"] + sorted(
        listings_df["state"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_listing_state = st.selectbox(
        "Filter by State",
        listing_states,
        key="listing_filter_state"
    )


# -----------------------------------------
# Region filter
# -----------------------------------------

with filter_col2:

    if selected_listing_state == "All":

        listing_regions = ["All"] + sorted(
            listings_df["region"]
            .dropna()
            .unique()
            .tolist()
        )

    else:

        listing_regions = ["All"] + sorted(
            listings_df.loc[
                listings_df["state"] == selected_listing_state,
                "region"
            ]
            .dropna()
            .unique()
            .tolist()
        )

    selected_listing_region = st.selectbox(
        "Filter by Region",
        listing_regions,
        key="listing_filter_region"
    )


# -----------------------------------------
# Apply filters
# -----------------------------------------

filtered_listings = listings_df.copy()

if selected_listing_state != "All":

    filtered_listings = filtered_listings[
        filtered_listings["state"] == selected_listing_state
    ]


if selected_listing_region != "All":

    filtered_listings = filtered_listings[
        filtered_listings["region"] == selected_listing_region
    ]


# -----------------------------------------
# Sort by valuation difference
# -----------------------------------------

filtered_listings = filtered_listings.sort_values(
    by="valuation_delta_pct",
    ascending=False
)


# -----------------------------------------
# Summary metrics
# -----------------------------------------

if not filtered_listings.empty:

    total_listings = len(filtered_listings)

    positive_count = (
        filtered_listings["valuation_delta"] > 0
    ).sum()

    average_delta = filtered_listings[
        "valuation_delta_pct"
    ].mean()

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric(
            "Listings",
            f"{total_listings:,}"
        )

    with metric_col2:
        st.metric(
            "Positive Model Difference",
            f"{positive_count:,}"
        )

    with metric_col3:
        st.metric(
            "Average Difference",
            f"{average_delta:.1f}%"
        )


# -----------------------------------------
# Prepare filtered table for display
# -----------------------------------------

display_df = filtered_listings.copy()

display_df["asking_price"] = display_df[
    "asking_price"
].map(
    lambda x: f"€{x:,.0f}"
)

display_df["predicted_price"] = display_df[
    "predicted_price"
].map(
    lambda x: f"€{x:,.0f}"
)

display_df["valuation_delta"] = display_df[
    "valuation_delta"
].map(
    lambda x: f"{x:+,.0f} €"
)

display_df["valuation_delta_pct"] = display_df[
    "valuation_delta_pct"
].map(
    lambda x: f"{x:+.1f}%"
)


# -----------------------------------------
# Rename columns
# -----------------------------------------

display_df = display_df.rename(
    columns={
        "source_listing_id": "Listing ID",
        "state": "State",
        "region": "Region",
        "living_space": "Living Space (m²)",
        "rooms": "Rooms",
        "year_built": "Year Built",
        "asking_price": "Asking Price",
        "predicted_price": "Model Estimate",
        "valuation_delta": "Difference",
        "valuation_delta_pct": "Difference %",
        "last_seen_at": "Last Seen",
    }
)


# -----------------------------------------
# Display listings
# -----------------------------------------

st.subheader("Model-Based Listing Comparison")

if display_df.empty:

    st.info(
        "No listings match the selected filters."
    )

else:

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
