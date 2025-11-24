#!/usr/bin/env python3
# code/machine_learning/per_fuse_minutely_forecast_xgboost.py
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# === Paths ===
project_root = Path(__file__).parent.parent.parent
data_path = project_root / "data" / "energy_fuse_archive.parquet"
models_dir = project_root / "models" / "per_fuse"
plots_dir = project_root / "results" / "plots" / "per_fuse"

models_dir.mkdir(parents=True, exist_ok=True)
plots_dir.mkdir(parents=True, exist_ok=True)

print(f"Loading data from: {data_path}")
df = pd.read_parquet(data_path)
df = df.sort_index()

print(f"Data range: {df.index.min()} → {df.index.max()}")
print(f"Total measurements: {len(df):,}")

fuses = df['entity_id'].unique()
print(f"Found {len(fuses)} fuses")

results = []

for fuse in fuses:
    print(f"\nTraining model for: {fuse}")
    
    # Extract fuse data
    fuse_data = df[df['entity_id'] == fuse].copy()
    if len(fuse_data) < 100:
        print(f"  → Skipping: only {len(fuse_data)} points")
        continue

    # Reindex to minutely, forward-fill missing
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='min')
    fuse_data = fuse_data.reindex(full_range, method='ffill').fillna(method='bfill')
    fuse_data = fuse_data.rename(columns={'value_w': 'power'})

    # Feature engineering — short lags only for small data
    df_feat = fuse_data[['power']].copy()
    df_feat['minute'] = df_feat.index.minute
    df_feat['hour'] = df_feat.index.hour
    df_feat['dayofweek'] = df_feat.index.dayofweek

    # Adaptive lags: use only what's possible
    max_lag = min(60, len(df_feat) // 4)
    for lag in [1, 5, 15, max_lag]:
        df_feat[f'lag_{lag}'] = df_feat['power'].shift(lag)
    
    df_feat['rolling_mean_30'] = df_feat['power'].rolling(30, min_periods=1).mean()
    df_feat = df_feat.dropna()

    if len(df_feat) < 50:
        print(f"  → Not enough data after features: {len(df_feat)}")
        continue

    # Train/test split
    split = int(0.8 * len(df_feat))
    train, test = df_feat.iloc[:split], df_feat.iloc[split:]

    X_train = train.drop('power', axis=1)
    y_train = train['power']
    X_test = test.drop('power', axis=1)
    y_test = test['power']

    print(f"  → Training on {len(train)} | Testing on {len(test)} minutes")

    # Light XGBoost for small data
    model = xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        random_state=42
    )
    model.fit(X_train, y_train, verbose=False)

    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))

    print(f"  → {fuse} | MAE: {mae:.1f}W | RMSE: {rmse:.1f}W")

    results.append({'fuse': fuse, 'mae': mae, 'rmse': rmse, 'points': len(fuse_data)})

    # Save model
    safe_name = fuse.replace("/", "_")
    model.save_model(models_dir / f"xgboost_{safe_name}.json")

    # Plot last 6 hours
    n = min(360, len(pred))
    plt.figure(figsize=(14, 5))
    plt.plot(y_test.index[-n:], y_test.values[-n:], label="Actual", linewidth=1.8)
    plt.plot(y_test.index[-n:], pred[-n:], label=f"Forecast (RMSE {rmse:.0f}W)", linewidth=1.8, alpha=0.9)
    plt.title(f"{fuse} — Last 6 Hours Minutely Forecast")
    plt.ylabel("Power (W)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / f"forecast_6h_{safe_name}.png", dpi=300)
    plt.close()

# === Summary ===
if results:
    results_df = pd.DataFrame(results).sort_values('rmse')
    print("\n" + "="*80)
    print("PER-FUSE MINUTELY FORECASTING RESULTS")
    print("="*80)
    print(results_df.to_string(index=False, float_format="%.1f"))
    results_df.to_csv(project_root / "results" / "per_fuse_results.csv", index=False)
else:
    print("\nNo fuse had enough data for training.")

print(f"\nModels → models/per_fuse/")
print(f"Plots → results/plots/per_fuse/")
