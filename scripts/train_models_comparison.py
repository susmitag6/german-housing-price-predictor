import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.decomposition import PCA

from xgboost import XGBRegressor
from sklearn.metrics import (
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
)


DATA_PATH = "data/processed/germany_housing.csv"

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

TARGET = "price"


# -----------------------------------------
# Load data
# -----------------------------------------

df = pd.read_csv(DATA_PATH)

print(f"Loaded {len(df):,} properties")

X = df[FEATURES]
y = df[TARGET]


# -----------------------------------------
# Train / test split
# -----------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# -----------------------------------------
# Numerical preprocessing
# -----------------------------------------

numeric_features = [
    "living_space",
    "rooms",
    "year_built",
    "lot_area",
]

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        ),
    ]
)


# -----------------------------------------
# Categorical preprocessing
# -----------------------------------------

categorical_features = [
    "state",
    "region",
    "condition",
    "building_type",
]

categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore")
        ),
    ]
)


# -----------------------------------------
# Combine preprocessing
# -----------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            numeric_features
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        ),
    ]
)

# -----------------------------------------
# pca_categorical preprocessing
# -----------------------------------------

pca_categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            )
        ),
    ]
)

pca_preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            numeric_features
        ),
        (
            "categorical",
            pca_categorical_pipeline,
            categorical_features
        ),
    ]
)


# -----------------------------------------
# Linear Regression
# -----------------------------------------

linear_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", LinearRegression()),
    ]
)

print("\nTraining Linear Regression...")

linear_model.fit(
    X_train,
    y_train
)


# -----------------------------------------
# Predictions
# -----------------------------------------

predictions = linear_model.predict(X_test)


# -----------------------------------------
# Evaluation
# -----------------------------------------

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = root_mean_squared_error(
    y_test,
    predictions
)

r2 = r2_score(
    y_test,
    predictions
)


print("\n" + "=" * 50)
print("LINEAR REGRESSION RESULTS")
print("=" * 50)

print(f"MAE:  €{mae:,.2f}")
print(f"RMSE: €{rmse:,.2f}")
print(f"R²:   {r2:.4f}")

# -----------------------------------------
# Random Forest
# -----------------------------------------

random_forest_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "model",
            RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        ),
    ]
)

print("\nTraining Random Forest...")

random_forest_model.fit(
    X_train,
    y_train
)

# -----------------------------------------
# Predictions
# -----------------------------------------

rf_predictions = random_forest_model.predict(X_test)



# -----------------------------------------
# Evaluation
# -----------------------------------------


rf_mae = mean_absolute_error(
    y_test,
    rf_predictions
)

rf_rmse = root_mean_squared_error(
    y_test,
    rf_predictions
)

rf_r2 = r2_score(
    y_test,
    rf_predictions
)


print("\n" + "=" * 50)
print("RANDOM FOREST RESULTS")
print("=" * 50)

print(f"MAE:  €{rf_mae:,.2f}")
print(f"RMSE: €{rf_rmse:,.2f}")
print(f"R²:   {rf_r2:.4f}")


# -----------------------------------------
# k-NN Regression
# -----------------------------------------

knn_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "model",
            KNeighborsRegressor(
                n_neighbors=10,
                weights="distance",
                n_jobs=-1
            )
        ),
    ]
)

print("\nTraining k-NN Regression...")

knn_model.fit(
    X_train,
    y_train
)

# -----------------------------------------
# Predictions
# -----------------------------------------

knn_predictions = knn_model.predict(X_test)


# -----------------------------------------
# Evaluation
# -----------------------------------------

knn_mae = mean_absolute_error(
    y_test,
    knn_predictions
)

knn_rmse = root_mean_squared_error(
    y_test,
    knn_predictions
)

knn_r2 = r2_score(
    y_test,
    knn_predictions
)


print("\n" + "=" * 50)
print("k-NN REGRESSION RESULTS")
print("=" * 50)

print(f"MAE:  €{knn_mae:,.2f}")
print(f"RMSE: €{knn_rmse:,.2f}")
print(f"R²:   {knn_r2:.4f}")

# -----------------------------------------
# XGBoost Regression
# -----------------------------------------

xgb_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "model",
            XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1
            )
        ),
    ]
)

print("\nTraining XGBoost...")

xgb_model.fit(
    X_train,
    y_train
)

# -----------------------------------------
# Predictions
# -----------------------------------------

xgb_predictions = xgb_model.predict(X_test)

# -----------------------------------------
# Evaluation
# -----------------------------------------

xgb_mae = mean_absolute_error(
    y_test,
    xgb_predictions
)

xgb_rmse = root_mean_squared_error(
    y_test,
    xgb_predictions
)

xgb_r2 = r2_score(
    y_test,
    xgb_predictions
)


print("\n" + "=" * 50)
print("XGBOOST RESULTS")
print("=" * 50)

print(f"MAE:  €{xgb_mae:,.2f}")
print(f"RMSE: €{xgb_rmse:,.2f}")
print(f"R²:   {xgb_r2:.4f}")

# -----------------------------------------
# PCA + Linear Regression
# -----------------------------------------

pca_linear_model = Pipeline(
    steps=[
        ("preprocessor", pca_preprocessor),

        (
            "pca",
            PCA(
                n_components=0.95,
                random_state=42
            )
        ),

        (
            "model",
            LinearRegression()
        ),
    ]
)


print("\nTraining PCA + Linear Regression...")



# -----------------------------------------
# Predictions
# -----------------------------------------
pca_linear_model.fit(
    X_train,
    y_train
)


pca_linear_predictions = pca_linear_model.predict(
    X_test
)

# -----------------------------------------
# Evaluation
# -----------------------------------------

pca_linear_mae = mean_absolute_error(
    y_test,
    pca_linear_predictions
)

pca_linear_rmse = root_mean_squared_error(
    y_test,
    pca_linear_predictions
)

pca_linear_r2 = r2_score(
    y_test,
    pca_linear_predictions
)


print("\n" + "=" * 50)
print("PCA + LINEAR REGRESSION RESULTS")
print("=" * 50)

print(f"MAE:  €{pca_linear_mae:,.2f}")
print(f"RMSE: €{pca_linear_rmse:,.2f}")
print(f"R²:   {pca_linear_r2:.4f}")


# -----------------------------------------
# PCA + k-NN
# -----------------------------------------

pca_knn_model = Pipeline(
    steps=[
        ("preprocessor", pca_preprocessor),

        (
            "pca",
            PCA(
                n_components=0.95,
                random_state=42
            )
        ),

        (
            "model",
            KNeighborsRegressor(
                n_neighbors=10,
                weights="distance",
                n_jobs=-1
            )
        ),
    ]
)


print("\nTraining PCA + k-NN...")


pca_knn_model.fit(
    X_train,
    y_train
)

# -----------------------------------------
# Predictions
# -----------------------------------------

pca_knn_predictions = pca_knn_model.predict(
    X_test
)

# -----------------------------------------
# Evaluation
# -----------------------------------------

pca_knn_mae = mean_absolute_error(
    y_test,
    pca_knn_predictions
)

pca_knn_rmse = root_mean_squared_error(
    y_test,
    pca_knn_predictions
)

pca_knn_r2 = r2_score(
    y_test,
    pca_knn_predictions
)

print("\n" + "=" * 50)
print("PCA + k-NN RESULTS")
print("=" * 50)

print(f"MAE:  €{pca_knn_mae:,.2f}")
print(f"RMSE: €{pca_knn_rmse:,.2f}")
print(f"R²:   {pca_knn_r2:.4f}")
# -----------------------------------------
# Model-Comparison
# -----------------------------------------


results = pd.DataFrame([
    {
        "Model": "Linear Regression",
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    },
    {
        "Model": "Random Forest",
        "MAE": rf_mae,
        "RMSE": rf_rmse,
        "R2": rf_r2
    },
    {
        "Model": "k-NN Regression",
        "MAE": knn_mae,
        "RMSE": knn_rmse,
        "R2": knn_r2
    },
    {
        "Model": "XGBoost",
        "MAE": xgb_mae,
        "RMSE": xgb_rmse,
        "R2": xgb_r2
    },
      {
        "Model": "PCA + Linear Regression",
        "MAE": pca_linear_mae,
        "RMSE": pca_linear_rmse,
        "R2": pca_linear_r2
    },
    {
        "Model": "PCA + KNN",
        "MAE": pca_knn_mae,
        "RMSE": pca_knn_rmse,
        "R2": pca_knn_r2
    }
])

results = results.sort_values(
    by="RMSE",
    ascending=True
)

print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(
    results.to_string(
        index=False,
        formatters={
            "MAE": lambda x: f"€{x:,.2f}",
            "RMSE": lambda x: f"€{x:,.2f}",
            "R2": lambda x: f"{x:.4f}"
        }
    )
)


# -----------------------------------------
# Save model comparison results
# -----------------------------------------

os.makedirs("models", exist_ok=True)

results.to_csv(
    "models/model_results.csv",
    index=False
)

print("\nModel results saved to models/model_results.csv")

# -----------------------------------------
# Best Model
# -----------------------------------------

model_objects = {
    "Linear Regression": linear_model,
    "Random Forest": random_forest_model,
    "k-NN Regression": knn_model,
    "XGBoost": xgb_model,
    "PCA + Linear Regression": pca_linear_model,
    "PCA + KNN": pca_knn_model,
}
best_model_name = results.iloc[0]["Model"]
best_model = model_objects[best_model_name]
print(f"\nBest model: {best_model_name}")


joblib.dump(
    best_model,
    "models/best_model.pkl"
)

print("Best model saved to models/best_model.pkl")
