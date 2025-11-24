#!/usr/bin/env python3
# code/machine_learning/nilm_minutely_detection.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# === Paths ===
project_root = Path(__file__).parent.parent.parent
data_path = project_root / "data" / "energy_fuse_archive.parquet"
plots_dir = project_root / "results" / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

print(f"Loading data from: {data_path}")
df = pd.read_parquet(data_path)
df = df.sort_index()

print(f"Data range: {df.index.min()} to {df.index.max()}")
print(f"Total measurements: {len(df):,}")

# Total power
total_power = df.groupby(df.index)['value_w'].sum().to_frame('total_power')
available_fuses = df['entity_id'].value_counts()
print(f"\nFuses with data:\n{available_fuses}")

# === Appliances ===
appliances = {
    'ams_linje6_p': ('Main Line (ams_linje6_p)', 500),
    '08_lysstikk2ndfloor1_active_power': ('2nd Floor Lights', 100),
    '03_solarinput63a_active_power': ('Solar Input', 300),
    '06_kjeller15a_active_power': ('Basement', 200),
    '05_kjokkenlys15a_active_power': ('Kitchen Lights', 50),
}

results = []

for fuse, (display_name, threshold) in appliances.items():
    if fuse not in df['entity_id'].unique():
        continue

    count = available_fuses[fuse]
    if count < 100:
        continue

    print(f"\nTraining NILM for: {display_name} ({fuse}) — {count} points")

    fuse_data = df[df['entity_id'] == fuse][['value_w']].copy()
    fuse_data = fuse_data.rename(columns={'value_w': 'app_power'})

    data = total_power.join(fuse_data, how='inner')
    if len(data) < 100:
        continue

    data['true_on'] = (data['app_power'] > threshold).astype(int)

    features = pd.DataFrame(index=data.index)
    features['total_power'] = data['total_power']
    features['hour'] = features.index.hour
    features['minute'] = features.index.minute
    features['dayofweek'] = features.index.dayofweek

    X = features
    y_true = data['true_on']

    clf = RandomForestClassifier(n_estimators=400, random_state=42, n_jobs=-1)
    clf.fit(X, y_true)

    y_pred = clf.predict(X)
    acc = accuracy_score(y_true, y_pred)
    print(f"  → {display_name}: {acc:.1%} accuracy")

    results.append({
        'Appliance': display_name,
        'Fuse': fuse,
        'Accuracy': acc,
        'Points': len(data),
        'Threshold_W': threshold
    })

    # === PLOT — LIGHT GREEN/YELLOW FOR PREDICTED ON ===
    plt.figure(figsize=(18, 9))
    
    ax1 = plt.gca()
    ax1.plot(data.index, data['total_power'], label='Total Power', color='gray', alpha=0.6, linewidth=1)
    ax1.set_ylabel("Total Power (W)", color='gray', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='gray')

    # True ON — dark green
    true_on_periods = data['true_on'] == 1
    ax1.fill_between(data.index, 0, data['total_power'].max(),
                     where=true_on_periods, color='#2ca02c', alpha=0.5, label='True ON')

    # Predicted ON — light green/yellow
    pred_on_periods = pd.Series(y_pred, index=data.index) == 1
    ax1.fill_between(data.index, 0, data['total_power'].max(),
                     where=pred_on_periods, color='#b2df8a', alpha=0.6, label='Predicted ON')

    ax1.set_title(f"TRUE MINUTELY NILM — {display_name}\n"
                  f"Entity ID: {fuse} | Accuracy: {acc:.1%} | Threshold: {threshold}W\n"
                  f"From Total Power Only", 
                  fontsize=18, pad=30, fontweight='bold')
    ax1.set_xlabel("Time", fontsize=14)
    ax1.legend(loc='upper left', fontsize=12)
    ax1.grid(True, alpha=0.3)

    # Appliance power
    ax2 = ax1.twinx()
    ax2.plot(data.index, data['app_power'], color='#1f77b4', linewidth=1.8, label='Appliance Power')
    ax2.axhline(threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold {threshold}W')
    ax2.set_ylabel(f"{display_name} Power (W)", color='#1f77b4', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#1f77b4')

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=11)

    plt.tight_layout()
    safe_name = fuse.replace("/", "_")
    plt.savefig(plots_dir / f"nilm_minutely_{safe_name}.png", dpi=300, bbox_inches='tight')
    plt.close()

# === Summary ===
if results:
    results_df = pd.DataFrame(results).sort_values('Accuracy', ascending=False)
    print("\n" + "="*80)
    print("MINUTELY TRUE NILM RESULTS — FROM TOTAL POWER ONLY")
    print("="*80)
    print(results_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.1%}" if x <= 1 else f"{x:.1f}"
    ))
    results_df.to_csv(project_root / "results" / "nilm_minutely_summary.csv", index=False)
else:
    print("\nNo appliances detected.")

print(f"\nPlots saved in {plots_dir}/")
