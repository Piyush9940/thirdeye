# Final Model Selection Report

## 1. Project

**Project:** NASA Earth Systems Trend Detective

**Selection status:** Provisional research selection

**Reference model:** Original MLP

**Operational deployment:** Not approved

## 2. Model selection decision

The original MLP is retained as the reference neural model because
it achieved the best equal-fold MAE and RMSE among the three models
in the original model-comparison experiment.

This is a provisional research decision. It does not establish
reliable methane forecasting capability.

## 3. Original model comparison

These results belong to the original model-comparison experiment.

- **Original MLP:** MAE = 53.786 ppb, RMSE = 56.872 ppb, R² = -13.345

- **Distance-weighted GCN:** MAE = 58.479 ppb, RMSE = 60.765 ppb, R² = -11.492

- **Unweighted GCN:** MAE = 70.934 ppb, RMSE = 75.871 ppb, R² = -23.944

- **Global training-mean baseline:** MAE = 62.717 ppb, RMSE = 65.066 ppb, R² = -11.899

## 4. Corrected feature ablation

These results belong to a separate reconstructed experiment.

- **Month-only MLP:** MAE = 49.039 ppb, RMSE = 52.684 ppb, R² = -10.486

The month-only model is retained as a diagnostic temporal reference.
Its input features are identical across spatial nodes within a period,
so it cannot reproduce spatial methane variation.

## 5. Fold-level evaluation

The evaluation periods were:

| Fold | Evaluation period | Evaluation observations |
|---|---|---:|
| 1 | February 2021 | 67 |
| 2 | August 2021 | 11 |
| 3 | November 2023 | 66 |

## 6. Model registry

| Model | Experiment | Decision |
|---|---|---|
| MLP | Original_model_comparison | Provisional reference model |\n| GCN_distance_weighted | Original_model_comparison | Research comparator |\n| GCN_unweighted | Original_model_comparison | Not selected |\n| Month_only | Reconstructed_three_way_ablation | Diagnostic temporal reference |\n| Climate_only | Reconstructed_three_way_ablation | Ablation comparator |\n| Climate_plus_month | Reconstructed_three_way_ablation | Not selected |\n| Global_training_mean | Prepared_fold_baseline | Naive baseline |\n
## 7. Scientific limitations

1. Only four methane observation periods are available: May 2019, February 2021, August 2021, and November 2023.\n2. August 2021 has only 11 evaluation observations.\n3. November 2023 has previously influenced model selection and is not an untouched final holdout.\n4. Most model-fold R2 values are negative. Reliable generalization has not been demonstrated.\n5. The month-only model produces the same prediction across spatial nodes within an evaluation period.\n6. The corrected three-way ablation uses a reconstructed Adam/MSE/full-batch training implementation. The original MLP optimizer and loss implementation were not recovered.\n7. Original model-comparison metrics and reconstructed ablation metrics must not be treated as a single controlled ranking because their training protocols are not confirmed to be identical.\n8. The current results do not establish causal relationships between climate variables and methane concentration.\n9. The current dataset is a pilot dataset and does not support claims of a validated long-term India methane forecast.\n10. An untouched future-period holdout and additional independent methane observations are required before operational use.\n
## 8. Next research requirements

1. Collect additional independent Sentinel-5P methane observations.
2. Increase the number of chronological evaluation periods.
3. Reserve a future-period holdout that is never used for model selection.
4. Re-evaluate the MLP and GNN using identical training and validation protocols.
5. Compare against seasonal, persistence, and training-mean baselines.
6. Investigate spatial residual patterns using verified geographic node IDs.
7. Report MAE, RMSE, R², bias, and uncertainty.
8. Only consider operational prediction after independent validation.

## 9. Final conclusion

The original MLP is retained as the provisional reference neural model.
The current experiments do not demonstrate a consistent advantage
from graph-based models.

The month-only model is the strongest reconstructed ablation reference,
but it is a period-level baseline rather than a spatial predictor.

The system should currently be presented as an exploratory research
prototype, not a validated methane forecasting system.
