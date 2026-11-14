# Model Reproducibility Report

Generated UTC: 2026-11-14T06:58:06.502488+00:00
Project root: `C:\Users\piyus\OneDrive\Desktop\nasa\earth-systems-trend-detective`

## Model selection

- Reference model: Original MLP
- Secondary diagnostic reference: Month-only MLP
- GNN advantage established: No
- Operational deployment approved: No

## Chronological evaluation

| Fold | Training periods | Evaluation period |
|---|---|---|
| 1 | May 2019 | February 2021 |
| 2 | May 2019, February 2021 | August 2021 |
| 3 | May 2019, February 2021, August 2021 | November 2023 |

Seeds: 7, 21, 42, 77, 123

## Software environment

- Python: 3.12.9
- Platform: Windows-11-10.0.26300-SP0
- PyTorch: 2.11.0+cu128
- CUDA available: True
- Device: NVIDIA GeForce RTX 3050 Laptop GPU

### Package versions

- torch: 2.11.0+cu128
- numpy: 2.5.4
- pandas: 3.0.2
- scikit-learn: 1.8.0
- scipy: 1.17.1
- networkx: 3.6.1
- pyarrow: 24.0.0

## Important experiment files

Files found: 16/16

| File | Exists | Size (bytes) |
|---|---:|---:|
| `reports/final_exploratory_experiment_config.json` | Yes | 1703 |
| `reports/final_model_comparison_corrected_fold_summary.csv` | Yes | 1266 |
| `reports/final_model_evaluation_predictions.csv` | Yes | 163493 |
| `reports/unified_baseline_seed_metrics.csv` | Yes | 12137 |
| `reports/unified_baseline_fold_comparison.csv` | Yes | 3845 |
| `reports/unified_baseline_overall_comparison.csv` | Yes | 942 |
| `reports/corrected_feature_ablation/corrected_three_way_ablation_predictions.csv` | Yes | 212635 |
| `reports/corrected_feature_ablation/corrected_three_way_ablation_overall_summary.csv` | Yes | 455 |
| `reports/corrected_feature_ablation/ablation_predictions_with_node_ids.csv` | Yes | 241796 |
| `reports/final_model_selection/final_model_selection_report.md` | Yes | 4452 |
| `reports/final_model_selection/final_model_selection_decision.json` | Yes | 6638 |
| `reports/final_model_selection/final_model_registry.csv` | Yes | 1523 |
| `data/processed/gnn_dataset/methane_climate_node_month_pilot.parquet` | Yes | 26629 |
| `data/processed/gnn_dataset/final_fold_1_prepared.npz` | Yes | 22575 |
| `data/processed/gnn_dataset/final_fold_2_prepared.npz` | Yes | 22549 |
| `data/processed/gnn_dataset/final_fold_3_prepared.npz` | Yes | 22544 |

## Model checkpoints

Checkpoint files discovered: 106

- `models\corrected_distance_weighted_gcn\fold_1_corrected_weighted_gcn_seed_123.pt` (4563 bytes)
- `models\corrected_distance_weighted_gcn\fold_1_corrected_weighted_gcn_seed_21.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_1_corrected_weighted_gcn_seed_42.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_1_corrected_weighted_gcn_seed_7.pt` (4543 bytes)
- `models\corrected_distance_weighted_gcn\fold_1_corrected_weighted_gcn_seed_77.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_2_corrected_weighted_gcn_seed_123.pt` (4563 bytes)
- `models\corrected_distance_weighted_gcn\fold_2_corrected_weighted_gcn_seed_21.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_2_corrected_weighted_gcn_seed_42.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_2_corrected_weighted_gcn_seed_7.pt` (4543 bytes)
- `models\corrected_distance_weighted_gcn\fold_2_corrected_weighted_gcn_seed_77.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_3_corrected_weighted_gcn_seed_123.pt` (4563 bytes)
- `models\corrected_distance_weighted_gcn\fold_3_corrected_weighted_gcn_seed_21.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_3_corrected_weighted_gcn_seed_42.pt` (4553 bytes)
- `models\corrected_distance_weighted_gcn\fold_3_corrected_weighted_gcn_seed_7.pt` (4543 bytes)
- `models\corrected_distance_weighted_gcn\fold_3_corrected_weighted_gcn_seed_77.pt` (4553 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_only_seed_123.pt` (4143 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_only_seed_21.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_only_seed_42.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_only_seed_7.pt` (4123 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_only_seed_77.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_plus_month_seed_123.pt` (4459 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_plus_month_seed_21.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_plus_month_seed_42.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_plus_month_seed_7.pt` (4439 bytes)
- `models\corrected_feature_ablation\fold_1_Climate_plus_month_seed_77.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_1_Month_only_seed_123.pt` (3867 bytes)
- `models\corrected_feature_ablation\fold_1_Month_only_seed_21.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_1_Month_only_seed_42.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_1_Month_only_seed_7.pt` (3847 bytes)
- `models\corrected_feature_ablation\fold_1_Month_only_seed_77.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_only_seed_123.pt` (4143 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_only_seed_21.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_only_seed_42.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_only_seed_7.pt` (4123 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_only_seed_77.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_plus_month_seed_123.pt` (4459 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_plus_month_seed_21.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_plus_month_seed_42.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_plus_month_seed_7.pt` (4439 bytes)
- `models\corrected_feature_ablation\fold_2_Climate_plus_month_seed_77.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_2_Month_only_seed_123.pt` (3867 bytes)
- `models\corrected_feature_ablation\fold_2_Month_only_seed_21.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_2_Month_only_seed_42.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_2_Month_only_seed_7.pt` (3847 bytes)
- `models\corrected_feature_ablation\fold_2_Month_only_seed_77.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_only_seed_123.pt` (4143 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_only_seed_21.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_only_seed_42.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_only_seed_7.pt` (4123 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_only_seed_77.pt` (4133 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_plus_month_seed_123.pt` (4459 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_plus_month_seed_21.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_plus_month_seed_42.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_plus_month_seed_7.pt` (4439 bytes)
- `models\corrected_feature_ablation\fold_3_Climate_plus_month_seed_77.pt` (4449 bytes)
- `models\corrected_feature_ablation\fold_3_Month_only_seed_123.pt` (3867 bytes)
- `models\corrected_feature_ablation\fold_3_Month_only_seed_21.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_3_Month_only_seed_42.pt` (3857 bytes)
- `models\corrected_feature_ablation\fold_3_Month_only_seed_7.pt` (3847 bytes)
- `models\corrected_feature_ablation\fold_3_Month_only_seed_77.pt` (3857 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_distance_weighted_seed_123.pt` (4425 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_distance_weighted_seed_21.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_distance_weighted_seed_42.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_distance_weighted_seed_7.pt` (4405 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_distance_weighted_seed_77.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_unweighted_seed_123.pt` (4355 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_unweighted_seed_21.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_unweighted_seed_42.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_unweighted_seed_7.pt` (4335 bytes)
- `models\final_exploratory_experiment\fold_1_GCN_unweighted_seed_77.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_1_MLP_seed_123.pt` (4245 bytes)
- `models\final_exploratory_experiment\fold_1_MLP_seed_21.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_1_MLP_seed_42.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_1_MLP_seed_7.pt` (4225 bytes)
- `models\final_exploratory_experiment\fold_1_MLP_seed_77.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_distance_weighted_seed_123.pt` (4425 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_distance_weighted_seed_21.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_distance_weighted_seed_42.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_distance_weighted_seed_7.pt` (4405 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_distance_weighted_seed_77.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_unweighted_seed_123.pt` (4355 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_unweighted_seed_21.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_unweighted_seed_42.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_unweighted_seed_7.pt` (4335 bytes)
- `models\final_exploratory_experiment\fold_2_GCN_unweighted_seed_77.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_2_MLP_seed_123.pt` (4245 bytes)
- `models\final_exploratory_experiment\fold_2_MLP_seed_21.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_2_MLP_seed_42.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_2_MLP_seed_7.pt` (4225 bytes)
- `models\final_exploratory_experiment\fold_2_MLP_seed_77.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_distance_weighted_seed_123.pt` (4425 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_distance_weighted_seed_21.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_distance_weighted_seed_42.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_distance_weighted_seed_7.pt` (4405 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_distance_weighted_seed_77.pt` (4415 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_unweighted_seed_123.pt` (4355 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_unweighted_seed_21.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_unweighted_seed_42.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_unweighted_seed_7.pt` (4335 bytes)
- `models\final_exploratory_experiment\fold_3_GCN_unweighted_seed_77.pt` (4345 bytes)
- `models\final_exploratory_experiment\fold_3_MLP_seed_123.pt` (4245 bytes)
- `models\final_exploratory_experiment\fold_3_MLP_seed_21.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_3_MLP_seed_42.pt` (4235 bytes)
- `models\final_exploratory_experiment\fold_3_MLP_seed_7.pt` (4225 bytes)
- `models\final_exploratory_experiment\fold_3_MLP_seed_77.pt` (4235 bytes)
- `outputs\model_training\best_gcn_gru_model.pth` (256141 bytes)

## Scientific limitations

- Only four methane observation months are available.
- August 2021 evaluation fold contains only 11 observations.
- November 2023 influenced model selection and is not an untouched holdout.
- Most evaluated models have negative R-squared values.
- No consistent GNN advantage has been demonstrated.
- Month-only predictions are period-level and not spatial predictions.
- The current results do not establish reliable long-term methane forecasting.
- Independent future observations are required for stronger validation.