# Sentinel-5P Methane Investigation

## Project overview

This package contains the documented and numerically audited results of an
exploratory Sentinel-5P methane investigation.

The investigation compares methane observations from 8 September 2019 and
9 September 2019 using 48 matched pixel pairs and examines associations
between methane differences and satellite observation geometry.

## Main findings

- 48 matched observations were analysed.
- Mean signed methane difference: +0.3339 ppb.
- Mean absolute methane difference: 10.7104 ppb.
- Solar-azimuth regression LOOCV RMSE: 10.3658 ppb.
- Leave-one-quadrant-out solar model RMSE: 10.2418 ppb.
- Leave-one-quadrant-out baseline RMSE: 15.7078 ppb.
- Pooled spatial RMSE improvement over baseline: 34.80%.
- Numerical reproduction audit: 8 of 8 tests passed.

## Package contents

| File | Purpose |
|---|---|
| ch4_cell116_audited_final_report.md | Main audited investigation report |
| ch4_cell113_final_investigation_report.md | Original investigation report |
| ch4_cell_34_78_matches_with_actual_geometry_angles.csv | Matched methane observations and geometry features |
| ch4_cell112_final_evidence_register.csv | Evidence register |
| ch4_cell112_scientific_limitations.txt | Scientific limitations |
| ch4_cell115_numerical_audit.csv | Numerical reproduction test results |
| ch4_cell117_artifact_inventory.csv | Artifact inventory |
| ch4_cell117_inventory_summary.txt | Inventory summary |

## Model description

The methane geometry experiment uses an exploratory linear regression
with solar azimuth difference as a predictor of matched methane
concentration difference.

It is not a deep-learning model or a GNN. It was evaluated using
leave-one-observation-out and leave-one-quadrant-out validation.

## Important scientific limitations

- The matched sample contains only 48 observations.
- The observations cover two dates, not a long-term methane time series.
- Spatial validation uses four sample-defined quadrants.
- The spatial test groups are small and uneven.
- Performance improvement is not uniform across all quadrants.
- Predictive association does not establish causation.
- The experiment does not establish India-wide or global predictive
  performance.
- Independent external validation on new observations has not been
  completed.

## Reproducibility

The numerical audit file records eight checks. All eight passed during
the reported audit.

The original project notebook and source satellite files are not included
in this compact handoff package. Consult the main project directory for
the complete data-processing workflow and source material.

## Interpretation

This is an exploratory satellite-data analysis and modelling experiment.
It should not be described as a validated operational methane-monitoring
or emissions-estimation system.
