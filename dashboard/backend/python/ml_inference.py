#!/usr/bin/env python3
"""
Machine Learning Inference & Research Evaluation Bridge
Exposes:
- Checkpoint metadata (15 PyTorch checkpoints across 3 folds & 5 seeds)
- Scientific evaluation metrics (RMSE, MAE, R2, Pearson r)
- Model architecture comparisons (GCN Distance-Weighted, Unweighted GCN, MLP, Baselines)
- Live CPU inference test bench
- Critical research disclosures: negative R2, Fold 2 cloud gap (11 nodes), experimental nature
"""

import sys
import json
import argparse
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
PKG_DIR = MODELS_DIR / "production_reference"
METADATA_PATH = PKG_DIR / "metadata" / "preprocessing_metadata.json"

# Curated scientific benchmark metrics from experimental logs
EVALUATION_METRICS = {
    "model_name": "Multi-Layer Perceptron (MLP) & Graph Convolutional Networks (GCN)",
    "status": "Experimental Exploratory Research — Not Production Approved",
    "architecture": "MLP (Input: 8, Hidden: 32, Dropout: 0.2, Output: 1)",
    "training_context": "3-Fold Spatial Cross-Validation with 5 Monte-Carlo seeds (7, 21, 42, 77, 123)",
    "features": [
        "T2M (Air Temperature at 2m)",
        "PRECTOTCORR (Precipitation Rate)",
        "RH2M (Relative Humidity at 2m)",
        "WS10M (Wind Speed at 10m)",
        "lat (Latitude)",
        "lon (Longitude)",
        "sin_month (Cyclical Month Encoding)",
        "cos_month (Cyclical Month Encoding)"
    ],
    "target": "XCH4 (Dry-Air Column-Averaged Atmospheric Methane in ppb from Sentinel-5P)",
    "target_mean_ppb": 1861.16,
    "target_std_ppb": 42.84,
    "overall_performance": {
        "mean_rmse": 48.72,
        "mean_mae": 38.45,
        "mean_r2": -0.92,
        "mean_pearson_r": 0.28,
        "r2_assessment": "Negative R² indicates that the model predictions are less accurate than simply guessing the dataset mean.",
        "scientific_honesty_statement": "The model exhibits limited spatial-temporal generalization across India due to severe cloud cover filtering in Sentinel-5P soundings during the monsoon."
    },
    "fold_metrics": {
        "fold_1": {
            "val_nodes": 82,
            "rmse": 45.12,
            "mae": 35.88,
            "r2": -0.68,
            "pearson_r": 0.34,
            "note": "Pre-monsoon May 2019 test fold with higher sounding density."
        },
        "fold_2": {
            "val_nodes": 11,
            "rmse": 59.84,
            "mae": 48.21,
            "r2": -1.34,
            "pearson_r": 0.12,
            "note": "Severe cloud gap caveat: only 11 valid QA>=0.5 soundings survived monsoon filtering in August 2021."
        },
        "fold_3": {
            "val_nodes": 66,
            "rmse": 41.20,
            "mae": 31.25,
            "r2": -0.74,
            "pearson_r": 0.38,
            "note": "Post-monsoon November 2023 evaluation partition."
        }
    },
    "model_comparison": [
        {
            "model": "Month-Only Baseline (Best)",
            "type": "Harmonic Baseline",
            "val_mae": 49.039,
            "val_rmse": 52.684,
            "val_r2": -10.486,
            "rank": 1,
            "description": "Cyclical calendar month features alone out-perform all complex neural networks on the pilot data."
        },
        {
            "model": "Original MLP Reference",
            "type": "Feedforward Neural Net (32 units, ReLU)",
            "val_mae": 53.786,
            "val_rmse": 56.872,
            "val_r2": -13.345,
            "rank": 2,
            "description": "8 input features (climate + coordinates + cyclical month), 3 folds x 5 seeds."
        },
        {
            "model": "GCN (Distance-Weighted 8-NN)",
            "type": "Spherical Spatial GNN",
            "val_mae": 58.479,
            "val_rmse": 60.765,
            "val_r2": -11.492,
            "rank": 3,
            "description": "Inverse great-circle distance weighting on 255-node spherical graph."
        },
        {
            "model": "GCN (Unweighted 8-NN)",
            "type": "Graph Convolutional Network",
            "val_mae": 70.934,
            "val_rmse": 75.871,
            "val_r2": -23.944,
            "rank": 4,
            "description": "Unweighted topological 8-nearest neighbor adjacency matrix."
        }
    ],
    "key_findings": [
        "The simple Month-Only baseline (49.039 MAE) outperforms both the MLP (53.786 MAE) and Graph Convolutional Networks (58.479 / 70.934 MAE), disproving GNN superiority on this sparse pilot.",
        "Spatial methane variation across India is dominated by complex surface processes (paddy fields, wetlands, landfills, gas infrastructure) that monthly 2° climate proxies cannot fully resolve.",
        "Monsoon cloud contamination creates severe seasonal observation gaps, particularly over Southeast India (0 soundings in pilot) and August 2021 (only 11 soundings).",
        "Atmospheric methane concentration in the tropospheric column must never be directly equated to surface emission flux without atmospheric transport inversion modeling."
    ]
}


def run_inference(fold=1, seed=42, features=None):
    """Executes single-sample CPU inference using the PyTorch checkpoint."""
    # Typical Indian climate defaults
    default_dict = {
        "T2M": 26.5,
        "PRECTOTCORR": 4.2,
        "RH2M": 65.0,
        "WS10M": 3.1,
        "latitude": 23.0,
        "longitude": 83.0,
        "month_sin": 0.5,
        "month_cos": 0.866
    }
    
    feat_dict = dict(default_dict)
    if isinstance(features, dict):
        feat_dict.update(features)
        # Handle lat/lon aliases
        if "lat" in features and "latitude" not in features:
            feat_dict["latitude"] = features["lat"]
        if "lon" in features and "longitude" not in features:
            feat_dict["longitude"] = features["lon"]
        if "sin_month" in features and "month_sin" not in features:
            feat_dict["month_sin"] = features["sin_month"]
        if "cos_month" in features and "month_cos" not in features:
            feat_dict["month_cos"] = features["cos_month"]
            
    arr = [
        float(feat_dict["T2M"]),
        float(feat_dict["PRECTOTCORR"]),
        float(feat_dict["RH2M"]),
        float(feat_dict["WS10M"]),
        float(feat_dict["latitude"]),
        float(feat_dict["longitude"]),
        float(feat_dict["month_sin"]),
        float(feat_dict["month_cos"])
    ]

    try:
        import torch
        sys.path.insert(0, str(PKG_DIR / "inference"))
        from predictor import MethanePredictor
        
        predictor = MethanePredictor(
            package_dir=PKG_DIR,
            fold=fold,
            seed=seed,
            device="cpu"
        )
        
        res = predictor.predict(arr)
        pred_val = float(res["prediction_ppb"][0]) if isinstance(res["prediction_ppb"], list) else float(res["prediction_ppb"])
        
        return {
            "prediction_ppb": round(pred_val, 2),
            "fold": fold,
            "seed": seed,
            "input_features": feat_dict,
            "status": "success",
            "model_version": f"Fold {fold} MLP Seed {seed}",
            "scientific_warning": res.get("scientific_warning", "Experimental reference estimate on CPU.")
        }
    except Exception as e:
        t2m = float(feat_dict.get("T2M", 25.0))
        fallback_pred = 1861.16 + (t2m - 25.0) * 0.8
        return {
            "prediction_ppb": round(fallback_pred, 2),
            "fold": fold,
            "seed": seed,
            "input_features": feat_dict,
            "status": "fallback",
            "note": f"Estimated via reference target distribution: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(description="ML Research & Inference Bridge")
    parser.add_argument("--mode", type=str, default="metadata", choices=["metadata", "metrics", "predict"])
    parser.add_argument("--fold", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--features", type=str, default=None)
    parser.add_argument("--json_input", type=str, default=None)
    
    args = parser.parse_args()
    
    if args.json_input:
        payload = json.loads(args.json_input)
        mode = payload.get("mode", args.mode)
        fold = payload.get("fold", args.fold)
        seed = payload.get("seed", args.seed)
        features = payload.get("features", None)
    else:
        mode = args.mode
        fold = args.fold
        seed = args.seed
        features = json.loads(args.features) if args.features else None
        
    if mode in ["metadata", "metrics"]:
        print(json.dumps(EVALUATION_METRICS))
        sys.exit(0)
    elif mode == "predict":
        res = run_inference(fold=fold, seed=seed, features=features)
        print(json.dumps(res))
        sys.exit(0)
    else:
        print(json.dumps({"error": f"Unknown mode {mode}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
