# NASA Earth Systems Trend Detective

## Corrected Master Scientific Validation Report

Generated: 2026-11-12T21:12:48.853371

## 1. Executive Summary

This project analyzes monthly meteorological conditions across 255 spatial grid nodes covering India from 2015 to 2024.

A spatial-temporal GCN-GRU model was trained to model four meteorological variables. Historical test performance was evaluated against a persistence baseline using the held-out 2024 period.

The project also performs spatial trend analysis, autocorrelation diagnostics, TFPW sensitivity analysis, and exploratory 2025 forecasting.

## 2. Dataset

| Property | Value |
|---|---|
| Source | NASA POWER |
| Region | India |
| Period | 2015-2024 |
| Monthly observations | 120 |
| Spatial nodes | 255 |
| Features | 4 |
| Tensor shape | (120, 255, 4) |

### Variables

| Feature | Unit |
|---|---|
| T2M | °C |
| PRECTOTCORR | mm/day |
| RH2M | % |
| WS10M | m/s |

PRECTOTCORR represents monthly mean daily precipitation, not monthly accumulated precipitation.

## 3. Spatial Graph

The graph uses a BallTree haversine K-nearest-neighbor construction with K=6, bidirectional connections, self-loops, and Gaussian distance weighting.

The model uses normalized symmetric adjacency during inference.
The graph describes geographic proximity and does not represent atmospheric transport.

## 4. GCN-GRU Model

| Property | Value |
|---|---|
| Architecture | GCN-GRU |
| Parameters | 20,292 |
| GCN hidden dimension | 32 |
| GRU hidden dimension | 64 |
| Sequence length | 12 months |
| Dropout | 0.15 |
| Training | 2015-2021 |
| Validation | 2022-2023 |
| Testing | 2024 |

Completed epochs: 100

Best validation epoch: 100

Best validation loss: 0.155307

## 5. Held-Out 2024 Model Evaluation

| Feature     | Unit   |   GCN_GRU_MAE |   GCN_GRU_RMSE |   GCN_GRU_R2 |   Persistence_MAE |   Persistence_RMSE |   Persistence_R2 |   MAE_Improvement_Percent |   RMSE_Improvement_Percent |
|:------------|:-------|--------------:|---------------:|-------------:|------------------:|-------------------:|-----------------:|--------------------------:|---------------------------:|
| T2M         | °C     |      1.54115  |       2.27894  |     0.971354 |          2.45336  |            3.36584 |         0.937514 |                   37.1818 |                    32.292  |
| PRECTOTCORR | mm/day |      1.3726   |       2.57887  |     0.731661 |          2.13434  |            3.75103 |         0.432292 |                   35.6897 |                    31.2489 |
| RH2M        | %      |      4.00459  |       5.63958  |     0.905205 |          5.73327  |            8.35718 |         0.791832 |                   30.1518 |                    32.5182 |
| WS10M       | m/s    |      0.518505 |       0.710005 |     0.824755 |          0.706114 |            1.04336 |         0.621563 |                   26.5693 |                    31.9503 |

The GCN-GRU outperformed the persistence baseline on MAE and RMSE for all four variables.

The 2024 evaluation uses rolling one-step-ahead predictions. It should not be confused with a 12-month free-running forecast.

## 6. Historical Trend Analysis

Seasonal Mann-Kendall testing, Sen slope estimation, and Benjamini-Hochberg FDR correction were applied across the 255 spatial nodes.

| feature     |   spatial_nodes |   mean_sen_slope |   median_sen_slope |   significant_nodes_after_fdr |   increasing_nodes_after_fdr |   decreasing_nodes_after_fdr |   alpha |
|:------------|----------------:|-----------------:|-------------------:|------------------------------:|-----------------------------:|-----------------------------:|--------:|
| T2M         |             255 |       0.0151895  |         0.0257816  |                            48 |                           47 |                            1 |    0.05 |
| PRECTOTCORR |             255 |       0.00764524 |         0.00231771 |                             3 |                            3 |                            0 |    0.05 |
| RH2M        |             255 |       0.268299   |         0.131423   |                            74 |                           69 |                            5 |    0.05 |
| WS10M       |             255 |      -0.00103082 |        -0.00173611 |                            17 |                            0 |                           17 |    0.05 |

The Sen slope values are reproduced as stored in the source report. Their exact time-unit convention should be confirmed from the trend-analysis implementation before assigning a per-year label.

### Interpretation

- T2M: 48 nodes were significant after FDR correction.
- PRECTOTCORR: 3 nodes were significant.
- RH2M: 74 nodes were significant.
- WS10M: 17 nodes were significant, all classified as decreasing in the original trend analysis.

These counts describe spatial nodes, not land-area percentages.

## 7. Autocorrelation and Trend Robustness

Lag-1 and seasonal lag-12 autocorrelation diagnostics indicated temporal dependence in the variables.

The following table compares significance overlap between the original analysis and the TFPW sensitivity analysis.

| feature     |   nodes |   original_significant_nodes |   tfpw_significant_nodes |   significant_in_both |   lost_significance |   newly_significant |   not_significant_in_either |   mean_centered_rho |   mean_uncentered_rho | robustness_label   |
|:------------|--------:|-----------------------------:|-------------------------:|----------------------:|--------------------:|--------------------:|----------------------------:|--------------------:|----------------------:|:-------------------|
| PRECTOTCORR |     255 |                            3 |                       26 |                     3 |                   0 |                  23 |                         229 |          -0.109173  |            -0.0347864 | Low node overlap   |
| RH2M        |     255 |                           74 |                       90 |                    68 |                   6 |                  22 |                         159 |          -0.106252  |            -0.0605539 | High node overlap  |
| T2M         |     255 |                           48 |                       61 |                    47 |                   1 |                  14 |                         193 |          -0.110936  |            -0.0662549 | High node overlap  |
| WS10M       |     255 |                           17 |                       22 |                    17 |                   0 |                   5 |                         233 |          -0.0970122 |            -0.0534532 | High node overlap  |

### Important interpretation

TFPW results are sensitivity results. Newly significant nodes must not be interpreted as stronger or more reliable trends.

Direction-agreement fields from the earlier robustness calculation are intentionally excluded because the direction comparison was not independent of the original Sen slope.

Only ten annual observations are available for each calendar month. Autocorrelation estimates and pre-whitening results therefore remain uncertain.

## 8. Exploratory 2025 Forecast

Forecast shape: (12, 255, 4)

Method: 12-month autoregressive GCN-GRU forecasting.

| Feature     | Unit   |    Minimum |   Maximum |     Mean |   Standard_Deviation |   Negative_Values |
|:------------|:-------|-----------:|----------:|---------:|---------------------:|------------------:|
| T2M         | °C     | -17.1759   |  37.3011  | 19.5889  |             13.2754  |               369 |
| PRECTOTCORR | mm/day |  -0.935331 |  29.5207  |  3.29845 |              3.74671 |               181 |
| RH2M        | %      |  18.4221   |  90.4398  | 65.0228  |             17.665   |                 0 |
| WS10M       | m/s    |   1.09669  |   8.66919 |  4.04532 |              1.56374 |                 0 |

### Numerical reproduction

- Maximum absolute difference: 0.004348755
- Mean absolute difference: 0.000032891
- Values within 0.001: 99.4608%
- Bit-for-bit identical: False

### Physical plausibility

Negative precipitation predictions: 181 / 3060 (5.9150%).

The minimum precipitation prediction is -0.935331 mm/day.

This violates physical non-negativity. The original model output is retained and the limitation is disclosed rather than silently clipping the predictions.

No independent 2025 observational dataset has been used to establish future forecast accuracy.

## 9. Validation Checklist

| Validation | Result |
|---|---|
| Four Variables Evaluated | PASS |
| Model Beats Persistence Mae | PASS |
| Model Beats Persistence Rmse | PASS |
| Trend Results Cover 255 Nodes | PASS |
| Forecast Dimensions Valid | PASS |
| Forecast Finite | PASS |
| Forecast Reproduction Within 0 001 | PASS |
| Precipitation Nonnegative | FAIL |

## 10. Scientific Limitations

- The 2024 test results measure historical held-out performance.
- The 2025 forecast has not been validated against observed 2025 data.
- Forecast numerical reproducibility does not establish forecast accuracy.
- Negative precipitation values violate physical non-negativity.
- The TFPW analysis is a sensitivity analysis, not a definitive correction.
- Direction-agreement columns from the earlier robustness output are excluded because their calculation is not an independent direction comparison.
- The historical record covers only ten years.
- Trend significance is subject to temporal autocorrelation and short-record uncertainty.
- Trend associations do not establish causal attribution.
- The geographic graph does not represent atmospheric transport.
- The model does not explicitly incorporate external climate forcing.
- The analysis uses four NASA POWER variables, not a comprehensive multi-source Earth-system dataset.

## 11. Conclusion

The project demonstrates a spatial-temporal GCN-GRU workflow for analyzing four NASA POWER meteorological variables across India using a 255-node geographic graph.

The model outperformed persistence on the held-out 2024 evaluation. The trend analysis identifies spatially varying statistical patterns, while autocorrelation and short-record limitations require cautious interpretation.

The 2025 forecast is exploratory, numerically reproducible within a close tolerance, and not independently validated against observed 2025 data. Negative precipitation predictions remain an unresolved physical constraint violation.

The appropriate scientific description is a research prototype for spatial-temporal meteorological trend exploration, not an operational climate prediction or causal-attribution system.
