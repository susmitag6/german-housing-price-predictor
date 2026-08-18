# German Housing Market Price Predictor

An end-to-end machine learning portfolio project that estimates German residential property prices and compares model estimates with newly ingested property asking prices.

The project combines historical German housing data, multiple regression models, PostgreSQL, third-party listing ingestion through Apify, automated scoring, and a Streamlit dashboard.

> **Important:** This is a portfolio project for my learning purpose, not a professional property valuation or investment recommendation system.

## Project Goal

Moving beyond model training, this project further demonstrates  how a trained model can be used with newly arriving housing listings.

The workflow is:

```text
Historical German Housing Data
        ↓
Preprocessing & Feature Engineering
        ↓
Model Training & Comparison
        ↓
Best Model: XGBoost
        ↓
New Listing Ingestion (Apify)
        ↓
Normalize & Validate
        ↓
PostgreSQL(Docker)
        ↓
Score New Listings
        ↓
Streamlit Dashboard
```

## Dataset

The training data comes from a German housing dataset downloaded from Kaggle (`apr20_price.csv`).

The original dataset contains many columns. To keep the portfolio project understandable, the model uses a smaller set of human-readable features:

- `living_space`
- `rooms`
- `year_built`
- `lot_area`
- `state`
- `region`
- `condition`
- `building_type`

Target:

- `purchase_price`

## Models Compared

I intentionally compared several different modeling approaches instead of jumping directly to one algorithm.

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| XGBoost | €162,859.45 | €282,231.84 | 0.6370 |
| Linear Regression | €170,962.20 | €302,288.12 | 0.5835 |
| k-NN Regression | €170,063.93 | €315,275.77 | 0.5470 |
| Random Forest | €183,627.21 | €315,466.94 | 0.5464 |
| PCA + Linear Regression | €193,755.75 | €330,766.83 | 0.5014 |
| PCA + k-NN | €182,407.84 | €331,911.31 | 0.4979 |

XGBoost produced the best overall test performance and is therefore used for scoring new listings.

## An Important Experiment: Adding Region

Before adding regional information, XGBoost achieved:

```text
R² = 0.4800
MAE = €192,571.70
RMSE = €337,762.67
```

After adding region:

```text
R² = 0.6370
MAE = €162,859.45
RMSE = €282,231.84
```

This was one of the most useful findings in the project. Housing prices are strongly location-dependent, so adding regional information gave the model substantially more predictive information.

## PCA Experiment

PCA was tested to see whether reducing correlated features would improve performance.

It did not improve the models in this experiment:

```text
Linear Regression R²       = 0.5835
PCA + Linear Regression R² = 0.5014

k-NN Regression R²         = 0.5470
PCA + k-NN R²              = 0.4979
```

This is still a useful result: dimensionality reduction is not automatically beneficial. PCA preserves feature variance, but the removed information may still be useful for predicting property prices.

## New Listing Ingestion

New listings are fetched through a third-party Apify actor and normalized into the feature structure expected by the project.

Example external values:

```text
Detached house       → single_family_house
In mint condition    → mint_condition
Completely renovated → fully_renovated
```
## 🐳 Docker

Docker is used to run the PostgreSQL database in an isolated and reproducible environment.

Instead of installing and configuring PostgreSQL directly on the host machine, the project runs PostgreSQL inside a Docker container.


The ingestion pipeline performs:

```text
Fetch
  ↓
Normalize
  ↓
Validate
  ↓
Upsert into PostgreSQL
```

New or changed listings can then be scored by the trained model.

## PostgreSQL

PostgreSQL provides persistent storage for incoming listings and model results.

Important fields include:

```text
source_listing_id
state
region
living_space
rooms
year_built
lot_area
condition
building_type
asking_price
predicted_price
valuation_delta
valuation_delta_pct
first_seen_at
last_seen_at
predicted_at
```

Existing listings are updated rather than blindly duplicated. If relevant listing information changes, the old prediction can be cleared so the property can be scored again.

## Listing Scoring

`score_listings.py` loads listings whose `predicted_price` is still empty, runs the trained XGBoost pipeline, calculates the model-versus-asking-price difference, and writes the results back to PostgreSQL.

```text
PostgreSQL
    ↓
Unscored listings
    ↓
XGBoost
    ↓
Predicted price
    ↓
Valuation difference
    ↓
PostgreSQL
```

The comparison metrics are:

```text
valuation_delta = predicted_price - asking_price
```

and:

```text
valuation_delta_pct =
(predicted_price - asking_price) / asking_price × 100
```

## Streamlit Dashboard

The dashboard contains:

### Price Predictor

Users can enter property characteristics and receive an estimated purchase price.

### Listing Filters

Listings can be filtered by state and region.

### Model-Based Listing Comparison

The current dashboard test shows:

```text
Listings:                  19
Positive Model Difference: 9
Average Difference:        23.6%
```

The table compares current asking prices with model estimates.

## How to Interpret the 23.6% Average Difference

The `23.6%` value should **not** be presented as proof that the properties are undervalued by 23.6%.

It is only the average difference between the model estimates and the asking prices for the currently displayed listings.

Possible reasons for a large difference include:

- prediction error;
- historical training data versus current listing conditions;
- differences between training and live-data distributions;
- missing property characteristics;
- imperfect category/location mapping between sources;
- asking prices not being the same as final transaction prices;
- third-party extraction/data-quality limitations;
- a small current live-listing sample;
- genuine pricing differences.

For this reason the application uses the wording **Model-Based Listing Comparison** rather than labels such as “Best Deals” or “Undervalued Properties.”

The live feed should also be described accurately as **third-party extracted listing data through Apify**, not as an official ImmoScout24 API feed or verified transaction-price data.

## Is This Truly Real-Time?

The application provides immediate predictions once a listing is available to the scoring pipeline, but the current ingestion process is run on demand.

A more precise description is:

> New-listing ingestion and near-real-time ML scoring.

A production extension could run ingestion on a schedule and automatically score newly detected listings.

## Project Structure

```text
Real-Time-Housing_Market_Price_Predictor/
│
├── app/
│   └── dashboard.py
│
├── data/
│   ├── raw/
│   │   └── apr20_price.csv
│   └── processed/
│
├── models/
│   └── best_model.pkl
│
├── scripts/
│   ├── preprocess.py
│   ├── explore.py
│   ├── train_models_comparison.py
│   ├── ingest.py
│   ├── score_listings.py
│   └── view_listings.py
│
├── sql/create_tables.sql 
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Environment Variables

Credentials are stored outside the source code.

Example `.env`:

```env
APIFY_TOKEN=your_apify_token

DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
```

Never commit `.env` to GitHub.

## Running the Project

### 1. Preprocess/train the model

Run the preprocessing/training scripts used by the project.

### 2. Ingest new listings

```bash
python scripts/ingest.py
```

### 3. Score new listings

```bash
python scripts/score_listings.py
```

### 4. Inspect stored listings

```bash
python scripts/view_listings.py
```

### 5. Start the dashboard

```bash
streamlit run app/dashboard.py
```

## Limitations

This project intentionally documents its limitations:

- Historical listing prices are not necessarily final transaction prices.
- Current listings come through a third-party extraction provider.
- External feature names/categories do not always exactly match the training dataset.
- Missing values and incomplete addresses can occur.
- The model uses a limited set of property characteristics.
- XGBoost R² is approximately 0.64, so substantial unexplained price variation remains.
- The current live-listing sample is small.
- Market conditions can change after the historical training period.
- A model/listing price difference is not an investment signal.
- Predictions are not professional valuations or financial advice.

## Future Improvements

Potential next steps include:

- scheduled ingestion;
- larger multi-city listing ingestion;
- stronger postcode/region normalization;
- more recent training data;
- time-aware train/test validation;
- hyperparameter tuning;
- prediction intervals;
- SHAP explanations;
- data-drift monitoring;
- model-performance monitoring;
- historical listing-price tracking;
- automated retraining.

## What I Learned

The main value of this project was learning how to connect the complete machine learning workflow:

```text
Data
→ preprocessing
→ experimentation
→ model evaluation
→ model selection
→ external ingestion
→ normalization
→ database
→ scoring
→ dashboard
```

Rather than presenting XGBoost as the entire project, the focus is on building a simple, understandable end-to-end ML system and being transparent about what its predictions do and do not mean.
# german-housing-price-predictor
