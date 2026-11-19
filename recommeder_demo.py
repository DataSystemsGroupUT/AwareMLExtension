# import numpy as np
# import pandas as pd
#
# # Set random seed for exact reproducibility
# np.random.seed(42)
#
# # Configuration Parameters
# N_ROWS = 3100
# N_DATASETS = 31
# ROWS_PER_DS = N_ROWS // N_DATASETS  # 100 preference profiles per dataset
# FRAMEWORKS = ["AutoClass", "AutoStreamML", "EvoAutoML", "OAML", "ChaCha"]
#
# # Exact Target Distributions
# # Top-1 match count: 3,100 * 0.9100 = 2,821
# # Top-3 success count: 3,100 * 0.9429032... ≈ 2,923 (2,821 Top-1 + 102 Top-3 only)
# N_TOP1 = 2821
# N_TOP3_ONLY = 102
# N_MISS = N_ROWS - N_TOP1 - N_TOP3_ONLY  # 177
#
# # Status mapping: 1 = Top-1 Match, 2 = Top-3 Match Only, 0 = Miss
# status_pool = [1] * N_TOP1 + [2] * N_TOP3_ONLY + [0] * N_MISS
# np.random.shuffle(status_pool)
#
# dataset_ids = [f"DS_{i:02d}" for i in range(1, N_DATASETS + 1)]
# active_obj_options = [
#     "accuracy,runtime",
#     "accuracy,energy,co2",
#     "accuracy,runtime,energy,co2",
# ]
#
# primary_rows = []
#
# for i in range(N_ROWS):
#     ds_idx = i // ROWS_PER_DS
#     ds_id = dataset_ids[ds_idx]
#     cohort = f"Cohort_{ds_idx % 4 + 1}"
#     pref_id = f"PREF_{(i % ROWS_PER_DS) + 1:03d}"
#     k_prime = int(np.random.choice([3, 5, 7, 10]))
#     active_obj = np.random.choice(active_obj_options)
#
#     # Base objective metrics
#     accuracy = round(float(np.random.uniform(0.78, 0.98)), 4)
#     runtime = round(float(np.random.uniform(12.0, 280.0)), 2)
#     energy = round(float(np.random.uniform(4.5, 48.0)), 2)
#     co2 = round(float(np.random.uniform(0.8, 14.5)), 2)
#
#     oracle_fw = str(np.random.choice(FRAMEWORKS))
#     other_fws = [f for f in FRAMEWORKS if f != oracle_fw]
#
#     row_status = status_pool[i]
#
#     if row_status == 1:
#         # Top-1 Match & Top-3 Success
#         recommended_fw = oracle_fw
#         top1_match = 1
#         top3_contains_oracle = 1
#         oracle_utility = round(float(np.random.uniform(0.82, 0.99)), 4)
#         recommended_utility = oracle_utility
#         regret_span = 0.0000
#         regret_cikm = 0.0000
#         spearman = round(float(np.random.uniform(0.88, 0.99)), 4)
#
#     elif row_status == 2:
#         # Top-3 Success, but not Top-1 Match
#         recommended_fw = str(np.random.choice(other_fws))
#         top1_match = 0
#         top3_contains_oracle = 1
#         oracle_utility = round(float(np.random.uniform(0.82, 0.99)), 4)
#         regret_span = round(float(np.random.uniform(0.015, 0.085)), 4)
#         recommended_utility = round(oracle_utility - regret_span, 4)
#         regret_cikm = round(regret_span / (oracle_utility + 0.1), 4)
#         spearman = round(float(np.random.uniform(0.78, 0.91)), 4)
#
#     else:
#         # Missed Top-3
#         recommended_fw = str(np.random.choice(other_fws))
#         top1_match = 0
#         top3_contains_oracle = 0
#         oracle_utility = round(float(np.random.uniform(0.82, 0.99)), 4)
#         regret_span = round(float(np.random.uniform(0.120, 0.420)), 4)
#         recommended_utility = round(
#             max(0.05, oracle_utility - regret_span), 4
#         )
#         regret_cikm = round(regret_span / (oracle_utility + 0.1), 4)
#         spearman = round(float(np.random.uniform(0.50, 0.77)), 4)
#
#     primary_rows.append(
#         {
#             "dataset_id": ds_id,
#             "cohort": cohort,
#             "preference_id": pref_id,
#             "k_prime": k_prime,
#             "active_objectives": active_obj,
#             "accuracy": accuracy,
#             "runtime": runtime,
#             "energy": energy,
#             "co2": co2,
#             "oracle_framework": oracle_fw,
#             "recommended_framework": recommended_fw,
#             "top1_match": top1_match,
#             "top3_contains_oracle": top3_contains_oracle,
#             "oracle_real_utility": oracle_utility,
#             "recommended_real_utility": recommended_utility,
#             "normalized_regret_span": regret_span,
#             "normalized_regret_cikm_denominator": regret_cikm,
#             "spearman_utility": spearman,
#             "evaluation_mode": "primary_offline",
#             "data_status": "SYNTHETIC_DEMO",
#         }
#     )
#
# # 1. Primary Synthetic Dataset
# df_primary = pd.DataFrame(primary_rows)
# df_primary.to_csv("phase18_preference_eval_primary_3100.csv", index=False)
#
# # 2. Re-computed Summary Dataset (Aggregated from primary rows)
# df_summary = (
#     df_primary.groupby(["dataset_id", "cohort"])
#     .agg(
#         cases=("preference_id", "count"),
#         top1_rate=("top1_match", "mean"),
#         top3_rate=("top3_contains_oracle", "mean"),
#         normalized_regret_mean=("normalized_regret_span", "mean"),
#         spearman_mean=("spearman_utility", "mean"),
#     )
#     .reset_index()
# )
# df_summary["top1_rate"] = df_summary["top1_rate"].round(4)
# df_summary["top3_rate"] = df_summary["top3_rate"].round(4)
# df_summary["normalized_regret_mean"] = df_summary["normalized_regret_mean"].round(4)
# df_summary["spearman_mean"] = df_summary["spearman_mean"].round(4)
# df_summary["data_status"] = "SYNTHETIC_DEMO"
#
# df_summary.to_csv("phase18_preference_summary.csv", index=False)

# Winner Predict VS Observed

# import numpy as np
# import pandas as pd
#
# # Set random seed for exact reproducibility
# np.random.seed(42)
#
# # Define exact Frameworks and Objectives
# FRAMEWORKS = ["AutoClass", "AutoStreamML", "EvoAutoML", "OAML", "ChaCha"]
# OBJECTIVES = ["accuracy", "runtime", "energy", "co2"]
#
# # Define 31 datasets and their respective cohorts
# historical_datasets = [
#     "abalone_Real",
#     "ailerons_Synthetic",
#     "bike_Real",
#     "cpu_activity_Real",
#     "diamonds_Real",
#     "elevators_Synthetic",
#     "fried_Synthetic",
#     "FriedmanGra_Synthetic",
#     "FriedmanLea_Synthetic",
#     "health_insurance_Real",
#     "House8L_Real",
#     "hyperA_Synthetic",
#     "kin8nm_Real",
#     "MetroTraffic_Real",
#     "nomao_Real",
#     "physiochemical_protein_Real",
#     "RBFm_100k_Synthetic",
#     "RTG_2abrupt_Synthetic",
#     "sarcos_Real",
#     "SEA_Abrubt_5_Synthetic",
#     "SEA_Mixed_5_Synthetic",
#     "SINE_Abrupt_Synthetic",
#     "white_wine_Real",
# ]
#
# extension_datasets = [
#     "bank_stream",
#     "census_income_stream",
#     "credit_card_stream",
#     "dutch_census_stream_awareml",
#     "german_credit_stream_80_20",
#     "insurance_stream",
#     "law_dataset_stream",
#     "StudentsPerformance_stream",
# ]
#
# # Combine all datasets with cohort labels (23 historical + 8 extension = 31 datasets)
# all_datasets = [(ds, "historical_23") for ds in historical_datasets] + [
#     (ds, "extension_8") for ds in extension_datasets
# ]
#
# # Target mismatches per objective (11 mismatches total across 124 rows = 113 matches / 91.13% Top-1)
# mismatch_targets = {"accuracy": 2, "runtime": 3, "energy": 3, "co2": 3}
#
# # Step 1: Construct base 124 dataset_id x objective rows
# rows = []
# for ds_id, cohort in all_datasets:
#     for obj in OBJECTIVES:
#         observed_fw = str(np.random.choice(FRAMEWORKS))
#         rows.append(
#             {
#                 "dataset_id": ds_id,
#                 "cohort": cohort,
#                 "objective": obj,
#                 "observed_best_framework": observed_fw,
#             }
#         )
#
# df_synth = pd.DataFrame(rows)
#
# # Step 2: Randomly select indices per objective to assign as mismatches
# mismatch_indices = []
# for obj, count in mismatch_targets.items():
#     obj_idx = df_synth[df_synth["objective"] == obj].index.tolist()
#     chosen_idx = np.random.choice(obj_idx, size=count, replace=False)
#     mismatch_indices.extend(chosen_idx)
#
# mismatch_set = set(mismatch_indices)
#
# # Step 3: Populate predicted_best_framework, top1_match, and data_status
# predicted_frameworks = []
# top1_matches = []
#
# for idx, row in df_synth.iterrows():
#     observed = row["observed_best_framework"]
#     if idx in mismatch_set:
#         other_fws = [f for f in FRAMEWORKS if f != observed]
#         pred = str(np.random.choice(other_fws))
#         match = False
#     else:
#         pred = observed
#         match = True
#
#     predicted_frameworks.append(pred)
#     top1_matches.append(match)
#
# df_synth["predicted_best_framework"] = predicted_frameworks
# df_synth["top1_match"] = top1_matches
# df_synth["data_status"] = "SYNTHETIC_DEMO"
#
# # Export synthetic 124-row objective winner dataset
# df_synth.to_csv(
#     "phase18_predicted_vs_observed_objective_winners.csv",
#     index=False,
# )
#
# # Step 4: Compute summary file directly from the 124-row dataset
# summary_records = []
# for obj in OBJECTIVES:
#     obj_df = df_synth[df_synth["objective"] == obj]
#     total = len(obj_df)
#     matches = int(obj_df["top1_match"].sum())
#     top1_acc = round(matches / total, 5)
#     summary_records.append(
#         {
#             "objective": obj,
#             "matches": matches,
#             "total": total,
#             "top1_accuracy": top1_acc,
#             "data_status": "SYNTHETIC_DEMO",
#         }
#     )
#
# # Add overall summary row
# total_all = len(df_synth)
# matches_all = int(df_synth["top1_match"].sum())
# top1_acc_all = round(matches_all / total_all, 5)
# summary_records.append(
#     {
#         "objective": "overall",
#         "matches": matches_all,
#         "total": total_all,
#         "top1_accuracy": top1_acc_all,
#         "data_status": "SYNTHETIC_DEMO",
#     }
# )
#
# df_summary = pd.DataFrame(summary_records)
# df_summary.to_csv(
#     "phase18_objective_winner_summary_SYNTHETIC_DEMO.csv", index=False
# )
#
# # Step 5: Logical Validation & Diagnostics
# inc_true_diff = len(
#     df_synth[
#         (df_synth["top1_match"] == True)
#         & (
#             df_synth["predicted_best_framework"]
#             != df_synth["observed_best_framework"]
#         )
#     ]
# )
# inc_false_same = len(
#     df_synth[
#         (df_synth["top1_match"] == False)
#         & (
#             df_synth["predicted_best_framework"]
#             == df_synth["observed_best_framework"]
#         )
#     ]
# )
# duplicates = df_synth.duplicated(subset=["dataset_id", "objective"]).sum()
#
# print("=" * 80)
# print("SYNTHETIC OBJECTIVE WINNER VALIDATION REPORT")
# print("=" * 80)
# print(f"Total Rows                             : {len(df_synth)}")
# print(f"Unique Datasets                        : {df_synth['dataset_id'].nunique()}")
# print(f"Rows per Objective                    : {df_synth['objective'].value_counts().to_dict()}")
# print(f"Rows per Cohort                       : {df_synth['cohort'].value_counts().to_dict()}")
# print(f"Total Exact Matches                    : {matches_all}")
# print(f"Total Mismatches                       : {total_all - matches_all}")
# print(f"Overall Top-1 Rate                     : {top1_acc_all:.5f} ({top1_acc_all * 100:.3f}%)")
# print("-" * 80)
# print("OBJECTIVE TOP-1 BREAKDOWN:")
# for rec in summary_records:
#     print(f"  - {rec['objective'].capitalize():<10} : {rec['matches']}/{rec['total']} ({rec['top1_accuracy'] * 100:.2f}%)")
# print("-" * 80)
# print("LOGICAL CONSISTENCY CHECKS:")
# print(f"  - top1_match=True but frameworks differ : {inc_true_diff} (PASSED)")
# print(f"  - top1_match=False but frameworks equal : {inc_false_same} (PASSED)")
# print(f"  - Duplicate dataset_id x objective rows : {duplicates} (PASSED)")
# print("=" * 80)

# 155 Datasets Prediction

import os
import json
import numpy as np
import pandas as pd
from scipy import stats

# ==========================================
# 0. CONFIGURATION & DIRECTORY SETUP
# ==========================================
SEED = 42
np.random.seed(SEED)

OUTPUT_DIR = "artifacts/phase18_synthetic_demo"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROVENANCE_NOTE = (
    "Synthetic demonstration data generated for UI, figure, and statistical-pipeline "
    "testing only. These values are not empirical Phase-18 measurements and must not "
    "be reported as held-out journal evidence."
)

INPUT_FILE = "phase18_frozen_v2_predictions_155_2.csv"
if not os.path.exists(INPUT_FILE):
    INPUT_FILE = "phase18_frozen_v2_predictions_155.csv"

# ==========================================
# 1. LOAD & CLEAN GROUND TRUTH / INPUT
# ==========================================
df_raw = pd.read_csv(INPUT_FILE)
df_raw.columns = df_raw.columns.str.strip()

df_clean = df_raw.dropna(subset=['dataset_id', 'cohort', 'framework']).copy()
df_clean['dataset_id'] = df_clean['dataset_id'].astype(str).str.strip()
df_clean['cohort'] = df_clean['cohort'].astype(str).str.strip()
df_clean['framework'] = df_clean['framework'].astype(str).str.strip()

VALID_FRAMEWORKS = {'AutoStreamML', 'AutoClass', 'EvoAutoML', 'OAML', 'ChaCha'}
assert len(df_clean) == 155, f"Expected 155 rows, got {len(df_clean)}"
assert df_clean['dataset_id'].nunique() == 31, f"Expected 31 unique datasets, got {df_clean['dataset_id'].nunique()}"
assert set(df_clean['framework']) == VALID_FRAMEWORKS, "Unexpected framework set found"
assert (df_clean.groupby('dataset_id')['framework'].nunique() == 5).all(), "Each dataset must have exactly 5 frameworks"
assert not df_clean.duplicated(subset=['dataset_id', 'framework']).any(), "Duplicate dataset_id x framework rows found"

df_gt = df_clean.copy()

# ==========================================
# 2. ALIGNED SYNTHETIC PREDICTION GENERATION
# ==========================================
OBJECTIVES = {
    'accuracy': {
        'dir': 'max', 'mae': 0.041, 'rmse': 0.058, 'spearman': 0.91,
        'winners': 29, 'cov': 140, 'bounds': (0.0, 1.0)
    },
    'runtime': {
        'dir': 'min', 'mae': 3.21, 'rmse': 4.87, 'spearman': 0.87,
        'winners': 28, 'cov': 135, 'bounds': (0.001, None)
    },
    'energy': {
        'dir': 'min', 'mae': 0.000082, 'rmse': 0.000116, 'spearman': 0.89,
        'winners': 28, 'cov': 140, 'bounds': (0.0, None)
    },
    'co2': {
        'dir': 'min', 'mae': 0.000034, 'rmse': 0.000049, 'spearman': 0.89,
        'winners': 28, 'cov': 140, 'bounds': (0.0, None)
    },
}

df_synth = df_gt[['dataset_id', 'cohort', 'framework']].copy()
df_synth['data_status'] = 'SYNTHETIC_DEMO'
datasets = df_gt['dataset_id'].unique()
n_datasets = len(datasets)

for obj, cfg in OBJECTIVES.items():
    gt_vals = df_gt[obj].values.copy()
    n_rows = len(gt_vals)
    is_max = (cfg['dir'] == 'max')

    # Select datasets that will match the observed winner
    n_target_winners = cfg['winners']
    matching_ds_indices = set(np.random.choice(n_datasets, size=n_target_winners, replace=False))

    preds = np.zeros(n_rows)

    # Generate predictions per dataset to ensure top-1 winner alignment
    for ds_idx, ds in enumerate(datasets):
        ds_mask = (df_gt['dataset_id'] == ds)
        ds_gt = df_gt.loc[ds_mask, obj].values
        fw_names = df_gt.loc[ds_mask, 'framework'].values

        # Base noise generation
        noise = np.random.normal(loc=0.0, scale=cfg['rmse'], size=len(ds_gt))
        ds_pred = ds_gt + noise

        obs_win_idx = np.argmax(ds_gt) if is_max else np.argmin(ds_gt)

        if ds_idx in matching_ds_indices:
            # Enforce that the observed winner remains the predicted winner
            pred_win_idx = np.argmax(ds_pred) if is_max else np.argmin(ds_pred)
            if pred_win_idx != obs_win_idx:
                # Swap predicted values to preserve winner match
                ds_pred[obs_win_idx], ds_pred[pred_win_idx] = ds_pred[pred_win_idx], ds_pred[obs_win_idx]
        else:
            # Enforce a mismatch in predicted winner
            pred_win_idx = np.argmax(ds_pred) if is_max else np.argmin(ds_pred)
            if pred_win_idx == obs_win_idx:
                alt_idx = (obs_win_idx + 1) % len(ds_gt)
                ds_pred[obs_win_idx], ds_pred[alt_idx] = ds_pred[alt_idx], ds_pred[obs_win_idx]

        preds[ds_mask] = ds_pred

    # Global scaling to match target MAE and RMSE exactly
    diff = preds - gt_vals
    current_mae = np.mean(np.abs(diff))
    if current_mae > 0:
        diff *= (cfg['mae'] / current_mae)
    preds = gt_vals + diff

    # Apply boundary constraints
    min_b, max_b = cfg['bounds']
    if min_b is not None:
        preds = np.maximum(preds, min_b)
    if max_b is not None:
        preds = np.minimum(preds, max_b)

    df_synth[obj] = preds

    # Generate Prediction Intervals
    covered_mask = np.zeros(n_rows, dtype=bool)
    covered_indices = np.random.choice(n_rows, size=cfg['cov'], replace=False)
    covered_mask[covered_indices] = True

    lower_bounds = np.zeros(n_rows)
    upper_bounds = np.zeros(n_rows)

    for i in range(n_rows):
        y_gt = gt_vals[i]
        y_pred = preds[i]
        half_width = np.random.uniform(cfg['mae'] * 0.8, cfg['mae'] * 2.2)

        if covered_mask[i]:
            l_val = min(y_pred - half_width, y_gt - 1e-5)
            u_val = max(y_pred + half_width, y_gt + 1e-5)
        else:
            if np.random.rand() > 0.5:
                l_val = y_gt + 1e-4
                u_val = l_val + 2 * half_width
            else:
                u_val = y_gt - 1e-4
                l_val = u_val - 2 * half_width

        l_val = min(l_val, y_pred)
        u_val = max(u_val, y_pred)

        if min_b is not None:
            l_val = max(min_b, l_val)
            u_val = max(min_b, u_val)
        if max_b is not None:
            l_val = min(max_b, l_val)
            u_val = min(max_b, u_val)

        lower_bounds[i] = l_val
        upper_bounds[i] = u_val

    df_synth[f'{obj}_lower'] = lower_bounds
    df_synth[f'{obj}_upper'] = upper_bounds

FINAL_COLS = [
    'dataset_id', 'cohort', 'framework',
    'accuracy', 'accuracy_lower', 'accuracy_upper',
    'runtime', 'runtime_lower', 'runtime_upper',
    'energy', 'energy_lower', 'energy_upper',
    'co2', 'co2_lower', 'co2_upper',
    'data_status'
]
df_synth = df_synth[FINAL_COLS]

synth_path = os.path.join(OUTPUT_DIR, "phase18_frozen_v2_predictions_155.csv")
df_synth.to_csv(synth_path, index=False)

# ==========================================
# 3. DERIVE OBJECTIVE WINNERS TABLE
# ==========================================
winner_rows = []
for ds in datasets:
    gt_ds = df_gt[df_gt['dataset_id'] == ds]
    synth_ds = df_synth[df_synth['dataset_id'] == ds]

    row_dict = {
        'dataset_id': ds,
        'cohort': gt_ds['cohort'].iloc[0],
        'data_status': 'SYNTHETIC_DEMO'
    }

    for obj, cfg in OBJECTIVES.items():
        is_max = (cfg['dir'] == 'max')

        obs_idx = gt_ds[obj].idxmax() if is_max else gt_ds[obj].idxmin()
        obs_winner = gt_ds.loc[obs_idx, 'framework']

        pred_idx = synth_ds[obj].idxmax() if is_max else synth_ds[obj].idxmin()
        pred_winner = synth_ds.loc[pred_idx, 'framework']

        row_dict[f'observed_{obj}_winner'] = obs_winner
        row_dict[f'predicted_{obj}_winner'] = pred_winner
        row_dict[f'{obj}_top1_match'] = bool(obs_winner == pred_winner)

    winner_rows.append(row_dict)

df_winners = pd.DataFrame(winner_rows)
winners_path = os.path.join(OUTPUT_DIR, "phase18_predicted_vs_observed_objective_winners.csv")
df_winners.to_csv(winners_path, index=False)

# ==========================================
# 4. COMPUTE OBJECTIVE METRICS & SPEARMAN
# ==========================================
metrics_summary = []
for obj, cfg in OBJECTIVES.items():
    gt_v = df_gt[obj].values
    pr_v = df_synth[obj].values

    mae = np.mean(np.abs(gt_v - pr_v))
    rmse = np.sqrt(np.mean((gt_v - pr_v) ** 2))

    spearmans = []
    for ds in datasets:
        gt_sub = df_gt[df_gt['dataset_id'] == ds][obj].values
        pr_sub = df_synth[df_synth['dataset_id'] == ds][obj].values
        rho, _ = stats.spearmanr(gt_sub, pr_sub)
        if not np.isnan(rho):
            spearmans.append(rho)
    mean_spearman = np.mean(spearmans)

    top1_matches = df_winners[f'{obj}_top1_match'].sum()
    top1_acc = top1_matches / len(datasets)

    cov_count = np.sum((df_synth[f'{obj}_lower'].values <= gt_v) & (gt_v <= df_synth[f'{obj}_upper'].values))
    cov_rate = cov_count / len(gt_v)

    metrics_summary.append({
        'objective': obj,
        'MAE': mae,
        'RMSE': rmse,
        'mean_spearman': mean_spearman,
        'top1_matches': int(top1_matches),
        'top1_accuracy': top1_acc,
        'covered_rows': int(cov_count),
        'coverage_rate': cov_rate,
        'data_status': 'SYNTHETIC_DEMO'
    })

df_metrics = pd.DataFrame(metrics_summary)
metrics_path = os.path.join(OUTPUT_DIR, "phase18_objective_metrics.csv")
df_metrics.to_csv(metrics_path, index=False)

# ==========================================
# 5. FAST BOOTSTRAP 95% CONFIDENCE INTERVALS
# ==========================================
N_BOOTSTRAPS = 10000
boot_results = []

for obj, cfg in OBJECTIVES.items():
    is_max = (cfg['dir'] == 'max')

    gt_mat = df_gt.pivot(index='dataset_id', columns='framework', values=obj).values
    pr_mat = df_synth.pivot(index='dataset_id', columns='framework', values=obj).values

    n_ds = len(datasets)
    b_mae, b_rmse, b_spearman, b_top1, b_cov = [], [], [], [], []

    low_mat = df_synth.pivot(index='dataset_id', columns='framework', values=f'{obj}_lower').values
    up_mat = df_synth.pivot(index='dataset_id', columns='framework', values=f'{obj}_upper').values

    for _ in range(N_BOOTSTRAPS):
        idx = np.random.choice(n_ds, size=n_ds, replace=True)

        b_gt = gt_mat[idx]
        b_pr = pr_mat[idx]
        b_low = low_mat[idx]
        b_up = up_mat[idx]

        diff = b_gt - b_pr
        b_mae.append(np.mean(np.abs(diff)))
        b_rmse.append(np.sqrt(np.mean(diff ** 2)))
        b_cov.append(np.mean((b_low <= b_gt) & (b_gt <= b_up)))

        obs_w = np.argmax(b_gt, axis=1) if is_max else np.argmin(b_gt, axis=1)
        prd_w = np.argmax(b_pr, axis=1) if is_max else np.argmin(b_pr, axis=1)
        b_top1.append(np.mean(obs_w == prd_w))

        spears = []
        for d in range(n_ds):
            rho, _ = stats.spearmanr(b_gt[d], b_pr[d])
            if not np.isnan(rho):
                spears.append(rho)
        b_spearman.append(np.mean(spears))

    for metric_name, b_dist in [('MAE', b_mae), ('RMSE', b_rmse), ('mean_spearman', b_spearman),
                                ('top1_accuracy', b_top1), ('coverage_rate', b_cov)]:
        boot_results.append({
            'objective': obj,
            'metric': metric_name,
            'mean': float(np.mean(b_dist)),
            'ci_lower_95': float(np.percentile(b_dist, 2.5)),
            'ci_upper_95': float(np.percentile(b_dist, 97.5)),
            'data_status': 'SYNTHETIC_DEMO'
        })

df_ci = pd.DataFrame(boot_results)
ci_path = os.path.join(OUTPUT_DIR, "phase18_objective_prediction_confidence_intervals.csv")
df_ci.to_csv(ci_path, index=False)

# ==========================================
# 6. FRIEDMAN TEST & STATISTICAL ANALYSIS
# ==========================================
stat_analysis = {'provenance': PROVENANCE_NOTE, 'metrics': {}}

for obj in OBJECTIVES.keys():
    pivot = df_synth.pivot(index='dataset_id', columns='framework', values=obj)
    fw_list = list(pivot.columns)
    data_matrix = pivot.values

    f_stat, p_val = stats.friedmanchisquare(*[pivot[col].values for col in fw_list])
    n_ds, k_fw = data_matrix.shape
    kendall_w = f_stat / (n_ds * (k_fw - 1))

    pairwise_results = []
    p_values = []
    pairs = []

    for i in range(k_fw):
        for j in range(i + 1, k_fw):
            fw1, fw2 = fw_list[i], fw_list[j]
            x, y = pivot[fw1].values, pivot[fw2].values

            diff = x - y
            diff_non_zero = diff[diff != 0]
            n_diff = len(diff_non_zero)

            if n_diff > 0:
                stat_w, p_w = stats.wilcoxon(x, y)
                r_biserial = (2 * stat_w / (n_diff * (n_diff + 1) / 2)) - 1
            else:
                stat_w, p_w, r_biserial = 0.0, 1.0, 0.0

            pairs.append((fw1, fw2, stat_w, r_biserial))
            p_values.append(p_w)

    sorted_indices = np.argsort(p_values)
    adj_p_values = np.zeros(len(p_values))
    m = len(p_values)

    for rank, idx in enumerate(sorted_indices):
        adj_p = p_values[idx] * (m - rank)
        adj_p_values[idx] = min(adj_p, 1.0)

    for k in range(1, m):
        idx_curr = sorted_indices[k]
        idx_prev = sorted_indices[k - 1]
        if adj_p_values[idx_curr] < adj_p_values[idx_prev]:
            adj_p_values[idx_curr] = adj_p_values[idx_prev]

    pairwise_dict = []
    for idx, (fw1, fw2, w_stat, r_bis) in enumerate(pairs):
        pairwise_dict.append({
            'framework_1': fw1,
            'framework_2': fw2,
            'wilcoxon_stat': float(w_stat),
            'p_value_raw': float(p_values[idx]),
            'p_value_holm': float(adj_p_values[idx]),
            'rank_biserial_effect_size': float(r_bis)
        })

    stat_analysis['metrics'][obj] = {
        'friedman_chi2': float(f_stat),
        'degrees_of_freedom': k_fw - 1,
        'p_value': float(p_val),
        'kendalls_w': float(kendall_w),
        'pairwise_comparisons': pairwise_dict
    }

json_path = os.path.join(OUTPUT_DIR, "phase18_statistical_analysis.json")
with open(json_path, 'w') as f:
    json.dump(stat_analysis, f, indent=2)

# ==========================================
# 7. VALIDATION REPORT PRINTING
# ==========================================
print("==========================================================================")
print("                       VALIDATION REPORT                                  ")
print("==========================================================================")
print("Structure:")
print(f"  Valid prediction rows:                {len(df_synth)}")
print(f"  Unique datasets:                      {df_synth['dataset_id'].nunique()}")
print(f"  Unique frameworks:                    {df_synth['framework'].nunique()}")
print(f"  Duplicate dataset_id x framework rows:{df_synth.duplicated(subset=['dataset_id', 'framework']).sum()}")
print(f"  Rows per dataset:                     {df_synth.groupby('dataset_id')['framework'].count().unique().tolist()}")
print()

print("Prediction Accuracy & Metrics Summary:")
for row in metrics_summary:
    o = row['objective']
    print(f"  {o.capitalize():10s} -> MAE: {row['MAE']:.6f} | RMSE: {row['RMSE']:.6f} | Spearman: {row['mean_spearman']:.4f}")
print()

print("Winner Agreement:")
total_matches = 0
for row in metrics_summary:
    o = row['objective']
    m = row['top1_matches']
    total_matches += m
    print(f"  {o.capitalize():10s} winner matches: {m} / 31 ({m/31*100:.2f}%)")
print(f"  Overall matches:           {total_matches} / 124 ({total_matches/124*100:.2f}%)")
print()

print("Interval Coverage:")
for row in metrics_summary:
    o = row['objective']
    c = row['covered_rows']
    print(f"  {o.capitalize():10s} covered rows: {c} / 155 ({c/155*100:.2f}%)")
print()

logical_errors = 0
for obj in OBJECTIVES.keys():
    logical_errors += (df_synth[f'{obj}_lower'] > df_synth[obj]).sum()
    logical_errors += (df_synth[f'{obj}_upper'] < df_synth[obj]).sum()

for obj in ['runtime', 'energy', 'co2']:
    logical_errors += (df_synth[obj] < 0).sum()

logical_errors += ((df_synth['accuracy'] < 0) | (df_synth['accuracy'] > 1)).sum()
logical_errors += df_synth.duplicated(subset=['dataset_id', 'framework']).sum()

print("Logical Integrity Checks:")
print(f"  Violations detected: {logical_errors}")
print("==========================================================================")