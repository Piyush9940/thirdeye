"""Inference service executing single and batch forward passes with exact preprocessing."""

import logging
from typing import Dict, Any, List
import numpy as np

from .schemas import PredictRequest, BatchPredictRequest, PredictResponse, BatchPredictResponse, FeatureDict
from .model_loader import model_loader

logger = logging.getLogger("model-service.inference")

SCIENTIFIC_WARNING = (
    "Not validated for operational methane forecasting. "
    "Interpret strictly within the original pilot-data scope."
)

SCIENTIFIC_DISCLOSURE = (
    "Notice: In empirical evaluations, the cyclical Month-Only baseline (MAE 49.039 ppb) "
    "outperformed the trained MLP (MAE 53.786 ppb) and Graph Convolutional Networks (58.479 / 70.934 ppb). "
    "The model exhibits negative R² on spatial validation folds. "
    "This endpoint serves an experimental research reference, NOT a causal surface emissions inventory."
)

FEATURE_NAMES = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "latitude",
    "longitude",
    "month_sin",
    "month_cos"
]

def extract_feature_list(features: Any) -> List[float]:
    """Converts a FeatureDict or list into an ordered 8-element float list."""
    if isinstance(features, FeatureDict):
        return features.to_ordered_list()
    elif isinstance(features, dict):
        fd = FeatureDict(**features)
        return fd.to_ordered_list()
    elif isinstance(features, (list, tuple)):
        if len(features) != 8:
            raise ValueError(f"Features list must contain exactly 8 elements. Received: {len(features)}")
        return [float(x) for x in features]
    else:
        raise ValueError(f"Unsupported features format: {type(features)}")

def run_single_prediction(request: PredictRequest) -> PredictResponse:
    """Executes single-sample prediction with the verified predictor."""
    feat_list = extract_feature_list(request.features)
    predictor = model_loader.get_predictor(request.fold, request.seed)
    
    # Execute inference using verified MethanePredictor
    result = predictor.predict(feat_list)
    
    raw_val = result["prediction_ppb"]
    pred_ppb = float(raw_val[0]) if isinstance(raw_val, (list, np.ndarray)) else float(raw_val)
    
    input_dict = {name: feat_list[i] for i, name in enumerate(FEATURE_NAMES)}
    
    return PredictResponse(
        prediction_ppb=round(pred_ppb, 4),
        output_unit="ppb",
        model="Original MLP Reference Model",
        fold=request.fold,
        seed=request.seed,
        status="experimental_reference",
        input_features=input_dict,
        scientific_warning=SCIENTIFIC_WARNING,
        scientific_disclosure=SCIENTIFIC_DISCLOSURE
    )

def run_batch_prediction(request: BatchPredictRequest) -> BatchPredictResponse:
    """Executes batch prediction using vectorized evaluation."""
    feature_matrix = [extract_feature_list(item) for item in request.items]
    predictor = model_loader.get_predictor(request.fold, request.seed)
    
    result = predictor.predict(feature_matrix)
    
    raw_vals = result["prediction_ppb"]
    if isinstance(raw_vals, (list, np.ndarray)):
        preds = [round(float(v), 4) for v in raw_vals]
    else:
        preds = [round(float(raw_vals), 4)]
        
    return BatchPredictResponse(
        count=len(preds),
        predictions_ppb=preds,
        fold=request.fold,
        seed=request.seed,
        output_unit="ppb",
        status="experimental_reference",
        scientific_warning=SCIENTIFIC_WARNING
    )
