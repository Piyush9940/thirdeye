# Machine Learning Experiments & Model Architecture

## 1. Selected Model: Original MLP Reference
- **Input Features (8):** T2M, PRECTOTCORR, RH2M, WS10M, Latitude, Longitude, Month Sine, Month Cosine.
- **Hidden Layers:** 1 linear layer with 32 units, ReLU non-linearity, Dropout rate $p = 0.20$.
- **Output:** 1 linear unit predicting standardized methane median concentration.
- **Optimization:** Adam optimizer, MSE loss, 250 training epochs.
- **Checkpoint Package:** 15 trained checkpoints across 3 temporal folds and 5 random seeds (7, 21, 42, 77, 123).

## 2. Benchmark Model Comparisons
Evaluation across 3 chronological validation folds:

1. **Month-only Diagnostic:** Equal-fold MAE 49.04 ppb, RMSE 52.68 ppb, R² -10.49.
2. **Original MLP:** Equal-fold MAE 53.79 ppb, RMSE 56.87 ppb, R² -13.35.
3. **Distance-Weighted GCN:** Equal-fold MAE 58.48 ppb, RMSE 60.76 ppb, R² -11.49.
4. **Global Training Mean:** Equal-fold MAE 62.72 ppb, RMSE 65.07 ppb, R² -11.90.
5. **Climate-only Ablation:** Equal-fold MAE 59.09 ppb, RMSE 63.26 ppb, R² -13.09.
6. **Unweighted GCN:** Equal-fold MAE 70.93 ppb, RMSE 75.87 ppb, R² -23.94.

## 3. Scientific Findings & Transparency
- Graph Neural Networks do not outperform the simple MLP architecture on this sparse dataset.
- Negative $R^2$ indicates predictions do not outperform the historical mean baseline across distant time horizons.
- The model status is strictly **Experimental Reference Model — Not Production Approved**.
