# Sentinel-5P Methane Comparison and Satellite Geometry Investigation

## 1. Executive Summary

This investigation examined methane observations from two Sentinel-5P
acquisition dates: 8 September 2019 and 9 September 2019.

The analysis focused on 48 spatially matched pixel pairs. It investigated
the differences between methane observations and examined whether satellite
viewing and solar geometry variables were associated with those differences.

Actual satellite geometry information was extracted from the corresponding
satellite-product data. Several statistical analyses, reduced regression
models, leave-one-observation-out tests and spatial holdout experiments
were performed.

The most notable exploratory result was a negative association between
solar azimuth difference and signed methane difference. A single-predictor
model retained a negative fitted slope in all four leave-one-quadrant-out
training experiments.

The pooled held-out RMSE was 10.2418 ppb for this model, compared with
15.7078 ppb for a training-mean baseline. This represents a 34.8% reduction
in pooled RMSE.

These findings are preliminary. They do not establish a causal satellite
geometry effect or demonstrate generalization to other dates or regions.

## 2. Study Design

### Data

- Satellite mission: Sentinel-5P
- Measured variable: methane (CH4)
- Acquisition dates: 8 September 2019 and 9 September 2019
- Matched observations: 48 pixel pairs
- Matching approach: mutual nearest-neighbour spatial matching
- Mean matching distance: approximately 3.149 km
- Maximum matching distance: approximately 6.190 km

The two acquisitions do not necessarily observe identical ground footprints.
The matched observations should therefore be interpreted as nearby spatial
comparisons rather than exact repeated measurements of the same physical
footprint.

### Difference convention

The signed methane difference is defined as:

CH4 difference = CH4 on 9 September 2019 - CH4 on 8 September 2019

Positive values indicate higher methane observations on the second date.
Negative values indicate lower methane observations on the second date.

## 3. Matched Methane Comparison

Across the 48 matched pairs:

- Mean signed difference: +0.334 ppb
- Standard deviation: 13.278 ppb
- Mean absolute difference: 10.710 ppb
- Root mean squared difference: 13.144 ppb
- Minimum difference: -27.024 ppb
- Maximum difference: +30.743 ppb

The small overall mean difference does not imply that individual matched
observations were similar. The relatively large spread and absolute
differences indicate substantial local variation within the matched sample.

These observations do not constitute an India-wide methane trend estimate.

## 4. Satellite Geometry Investigation

Actual viewing and solar geometry arrays were extracted from the
Sentinel-5P product data.

All 48 matched observations had valid values for the four geometry
angles on both acquisition dates.

The investigation examined:

- Viewing zenith difference
- Viewing azimuth difference
- Solar zenith difference
- Solar azimuth difference
- Spatial matching distance

### Geometry associations

Spearman correlations with signed methane difference were:

| Geometry variable | Spearman correlation |
|---|---:|
| Matching distance | +0.3290 |
| Viewing zenith difference | +0.5473 |
| Viewing azimuth difference | +0.5640 |
| Solar zenith difference | -0.0168 |
| Solar azimuth difference | -0.5897 |

The associations with absolute methane differences were substantially
weaker.

These results indicate associations within the selected sample. They
do not demonstrate that geometry caused the methane differences.

### Multicollinearity

The geometry variables were not independent of one another. In particular,
viewing zenith and viewing azimuth showed near-perfect correlation in the
selected sample.

This makes it difficult to isolate individual geometry effects using
large simultaneous regression models.

A reduced predictor approach was therefore preferred.

## 5. Reduced Solar Geometry Model

A single-predictor model using solar azimuth difference was evaluated
against other reduced geometry combinations.

For the 48-observation leave-one-out comparison, the solar-azimuth model
achieved:

- MAE: 7.9635 ppb
- RMSE: 10.3658 ppb

It performed better than the other tested reduced predictor combinations
in this comparison.

The result supports further investigation of solar azimuth as a
potential predictive feature. It does not establish a physical mechanism
or prove that solar azimuth directly influences measured methane.

## 6. Spatial Generalization Experiment

A leave-one-quadrant-out experiment was conducted using four spatial
quadrants.

The quadrants were defined using the sample median latitude and longitude.

| Held-out quadrant | Training observations | Test observations |
|---|---:|---:|
| North-East | 30 | 18 |
| North-West | 42 | 6 |
| South-East | 42 | 6 |
| South-West | 30 | 18 |

The solar-azimuth model produced a negative fitted slope in all four
training folds.

### Pooled held-out performance

| Metric | Solar-azimuth model | Baseline |
|---|---:|---:|
| MAE | 7.8627 ppb | 12.8822 ppb |
| RMSE | 10.2418 ppb | 15.7078 ppb |

The pooled RMSE improvement was approximately 34.8%.

The model improved RMSE in three of the four held-out quadrants.
The South-East quadrant showed essentially no improvement.

This indicates that the predictive benefit was not spatially uniform.

The four-fold experiment is useful exploratory evidence, but it is not
independent external validation. The quadrant boundaries were calculated
using the complete sample, and two test quadrants contained only six
observations each.

## 7. Separate Rank-Based Prediction Experiment

A separate modelling experiment evaluated the prediction of rank-based
methane differences.

In that experiment:

- Solar geometry achieved pooled MAE 0.2107 and RMSE 0.2553.
- Geographic-plus-solar achieved the best equal-weight quadrant RMSE
  of 0.2572.
- Cross-fitted calibration worsened MAE for all seven evaluated models.
- Raw predictions were retained instead of applying the tested
  calibration correction.

These rank-scale metrics are not methane concentration errors in ppb.
They represent a separate prediction task and should not be combined
numerically with the ppb-based results above.

## 8. Main Findings

1. Actual satellite geometry information was successfully extracted for
   all 48 matched observations.

2. Geometry variables showed substantial interdependence, limiting the
   interpretation of individual regression coefficients.

3. Solar azimuth difference had a negative Spearman association with
   signed methane difference in the selected sample.

4. The negative fitted solar-azimuth slope persisted across all four
   leave-one-quadrant-out training folds.

5. The solar-azimuth model reduced pooled spatial holdout RMSE by
   approximately 34.8% relative to the baseline.

6. Predictive improvement was not consistent across all four quadrants.

7. Rank-based prediction and ppb-based methane comparison are distinct
   analyses and must be reported separately.

## 9. Limitations

- Only 48 matched pixel pairs were available.
- The observations came from two acquisition dates in September 2019.
- The matched sample is not representative of India as a whole.
- Nearby matched pixels are not necessarily identical ground footprints.
- Geometry variables are strongly interdependent.
- Correlation and prediction do not establish causation.
- Only four spatial blocks were used for spatial holdout.
- Two quadrants contained only six observations each.
- Quadrant boundaries were calculated from the complete sample.
- The investigation does not independently validate the results using
  ground-based methane measurements.
- Two dates cannot establish a long-term methane trend.
- Performance on these observations does not establish generalization
  to other dates, seasons or geographic regions.

## 10. Recommended Future Work

1. Extend the comparison to many more Sentinel-5P acquisition dates.
2. Develop a larger matched-pixel dataset with stricter footprint
   and quality-control requirements.
3. Repeat spatial validation using predefined geographic blocks.
4. Test temporal holdout experiments on dates not used for model fitting.
5. Investigate geometry effects while explicitly accounting for
   spatial and temporal dependence.
6. Compare the results with independent methane observations where
   suitable validation data are available.
7. Examine whether the observed association persists across seasons
   and different geographic regions.
8. Investigate nonlinear models only after a larger and more
   representative dataset is assembled.

## 11. Conclusion

The Sentinel-5P investigation identified an exploratory association
between satellite solar azimuth difference and signed methane differences
in a set of 48 spatially matched observations from 8 and 9 September 2019.

The negative fitted relationship persisted across four spatial training
folds, and the model reduced pooled held-out RMSE relative to a
training-mean baseline.

However, the limited sample size, small spatial test groups, geometry
collinearity and two-date study design restrict the strength and scope
of the conclusions.

The results motivate a larger multi-date investigation rather than
supporting a claim of a confirmed causal geometry effect or a general
India-wide methane trend.

---

**Report status:** Exploratory research report  
**Analysis coverage:** Cells 89–112  
**Primary sample:** 48 matched observations  
**Satellite comparison dates:** 8–9 September 2019
