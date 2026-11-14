# NASA Space Apps Challenge — Research Report

## Executive Summary
This project investigates spatial, temporal, and climatic patterns in atmospheric methane ($X\text{CH}_4$) across India. Using Sentinel-5P TROPOMI Level-3 products and NASA POWER meteorology, we established a reproducible 255-node spatial framework and tested chronological machine learning benchmarks across 3 folds and 5 seeds.

## Core Conclusions
1. The simplest seasonal diagnostic (Month-only MLP) achieved the best predictive accuracy (MAE 49.04 ppb).
2. Complex Graph Neural Networks (GCN) did not provide an advantage on this sparse pilot dataset.
3. Satellite column concentration cannot be conflated with ground emissions without inverse transport modeling.
4. Future investigations require continuous multi-year time series and multi-gas co-registration.
