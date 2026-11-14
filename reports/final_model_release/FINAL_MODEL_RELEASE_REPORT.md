# NASA Earth Systems Trend Detective
# Final Model Release Report

## 1. Release Information

- Release: Experimental MLP Reference Model
- Version: 1.0.0-documentation
- Generated (UTC): 2026-11-14T07:29:43.032210+00:00
- Status: EXPERIMENTAL REFERENCE
- Production deployment approved: NO

This release documents the experimental methane estimation workflow,
its model artifacts, reproducibility information and scientific limitations.

## 2. Project Objective

The project investigates geographical and temporal patterns in atmospheric
methane observations over India by combining satellite methane measurements,
climate variables and spatial information.

The objective is to support environmental research and exploration.
This release does not claim operational methane forecasting capability.

## 3. Data Summary

- QA-filtered methane pixels: 73,045
- Unique satellite granules: 7
- Methane node-month observations: 226
- Spatial graph nodes: 255
- Observation months: 2019-05, 2021-02, 2021-08, 2023-11

Methane observations were quality filtered and associated with spatial nodes.
Climate information includes temperature, precipitation, relative humidity
and wind speed.

## 4. Model Architecture

Selected experimental reference: Original MLP

- Input features: 8
- Hidden units: 32
- Activation: ReLU
- Dropout: 0.2
- Output: methane concentration estimate in ppb
- Training epochs: 250

Feature order:

1. T2M
2. PRECTOTCORR
3. RH2M
4. WS10M
5. latitude
6. longitude
7. month_sin
8. month_cos

The checkpoint package contains fold-specific models for five random seeds.

## 5. Model Evaluation

Reported equal-fold mean metrics:

| Model | MAE (ppb) | RMSE (ppb) | R² |
|---|---:|---:|---:|
| Distance-weighted GCN | 58.479 | 60.765 | -11.492 |
| Unweighted GCN | 70.934 | 75.871 | -23.944 |
| Original MLP | 53.786 | 56.872 | -13.345 |
| Month-only ablation | 49.039 | 52.684 | -10.486 |

The metrics indicate weak predictive performance.
The experiments do not establish an advantage for graph-based learning.

## 6. Reproducibility Verification

- Expected original MLP checkpoints: 15
- Checkpoints currently found: 15
- Required release assets present: 39/39
- Historical saved prediction rows compared: 720
- Rows within 1e-4 ppb: 719
- Maximum absolute difference: 0.0001220703 ppb
- Mean absolute difference: 0.0000001695 ppb
- Prediction correlation: 1.0

The historical reproduction differences are extremely small and consistent
with floating-point numerical variation. The strict tolerance was not met
for every row.

The reusable predictor passed its direct-inference comparison test on
the tested samples. This verifies the implementation, not predictive skill.

## 7. Scientific Limitations

1. Only four methane observation months are available.
2. The data do not provide continuous monthly coverage.
3. August 2021 contains only 11 evaluation nodes.
4. Many November 2023 test locations were previously observed in training.
5. November 2023 influenced model selection and is not an independent holdout.
6. Most R² values are negative.
7. No reliable future forecasting skill has been demonstrated.
8. No GNN advantage has been established.
9. Climate associations must not be interpreted as causal relationships.
10. Methane concentration measurements alone do not identify emission sources.
11. Unobserved spatial nodes must remain missing, not zero.

## 8. Model Selection Decision

The Original MLP is retained as an experimental reference model because
its checkpoint architecture, preprocessing and inference implementation
have been reconstructed and verified.

The month-only MLP is retained as a diagnostic comparison.

Neither model is approved for operational environmental forecasting.

## 9. Dashboard Integration

The dashboard export pipeline generated spatial nodes, methane observations,
MLP predictions, fold-level metrics, fold summaries, GeoJSON and metadata.

The dashboard must preserve fold and seed identifiers, distinguish
observations from predictions, and clearly mark missing observations.

Predictions and environmental explanations must not be presented as
verified emission measurements.

## 10. Release Files

- model_release_manifest.json
- release_file_inventory.csv
- FINAL_MODEL_RELEASE_REPORT.md

The inventory contains SHA-256 checksums for the available release assets.

## 11. Future Research Requirements

Before making stronger forecasting claims, future work should include:

- More frequent and consistently sampled methane observations.
- Independent future-period holdout evaluation.
- Rolling-origin temporal validation.
- Stronger baselines and uncertainty quantification.
- Improved spatial and meteorological matching.
- Additional validation of source attribution and emission estimates.

## 12. Final Conclusion

The project has an implemented experimental satellite-data processing,
spatial analysis, machine-learning evaluation and dashboard-export pipeline.

The reference model and inference artifacts have been packaged and checked.
However, the current dataset and evaluation results do not justify
operational deployment or reliable future methane forecasting.

**Final release classification: EXPERIMENTAL REFERENCE MODEL — NOT
APPROVED FOR PRODUCTION DEPLOYMENT.**
