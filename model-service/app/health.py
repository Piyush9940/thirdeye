"""Health and metadata providers for the ML service."""

import sys
from datetime import datetime, timezone
import torch

from .config import settings
from .schemas import HealthResponse, MetadataResponse, ArchitectureSpec
from .model_loader import model_loader

SCIENTIFIC_LIMITATIONS = [
    "Only four methane observation months are available in the pilot dataset (May 2019, Feb 2021, Aug 2021, Nov 2023).",
    "Continuous monthly coverage does not exist across the 2019-2024 timeframe.",
    "August 2021 (Fold 2) contains only 11 valid spatial nodes due to severe monsoon cloud contamination.",
    "Southeast India had 0 valid Sentinel-5P soundings surviving optical QA filtering (QA >= 0.50).",
    "Reported spatial validation R² is negative across all evaluated folds.",
    "The Month-Only cyclical baseline (MAE 49.039 ppb) outperformed the MLP (MAE 53.786 ppb) and GCNs (58.479 / 70.934 ppb).",
    "No proven future forecasting skill or Graph Neural Network superiority has been established.",
    "Atmospheric column concentrations (ppb) do not equal surface methane emissions flux."
]

BENCHMARK_COMPARISON = [
    {
        "rank": 1,
        "model": "Month-Only Baseline (Best)",
        "type": "Harmonic Baseline",
        "val_mae_ppb": 49.039,
        "val_rmse_ppb": 52.684,
        "val_r2": -10.486,
        "description": "Harmonic calendar features alone out-perform all neural networks."
    },
    {
        "rank": 2,
        "model": "Original MLP Reference",
        "type": "Feedforward Neural Network (32 units, ReLU)",
        "val_mae_ppb": 53.786,
        "val_rmse_ppb": 56.872,
        "val_r2": -13.345,
        "description": "Production reference model wrapped by this inference service."
    },
    {
        "rank": 3,
        "model": "GCN (Distance-Weighted 8-NN)",
        "type": "Spherical Spatial GNN",
        "val_mae_ppb": 58.479,
        "val_rmse_ppb": 60.765,
        "val_r2": -11.492,
        "description": "Inverse great-circle distance weighting on 255-node graph."
    },
    {
        "rank": 4,
        "model": "GCN (Unweighted 8-NN)",
        "type": "Graph Convolutional Network",
        "val_mae_ppb": 70.934,
        "val_rmse_ppb": 75.871,
        "val_r2": -23.944,
        "description": "Unweighted topological 8-nearest neighbor adjacency matrix."
    }
]

def check_service_health() -> HealthResponse:
    """Verifies service health, PyTorch environment, and checkpoint integrity."""
    scan = model_loader.scan_checkpoints()
    total_found = scan["total_found"]
    
    if total_found == 15:
        status_str = "healthy"
    elif total_found > 0:
        status_str = "degraded"
    else:
        status_str = "unhealthy"
        
    return HealthResponse(
        status=status_str,
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        python_version=sys.version.split()[0],
        pytorch_version=torch.__version__,
        device=settings.INFERENCE_DEVICE,
        checkpoints_found=total_found,
        checkpoints_expected=15,
        all_checkpoints_loaded=scan["all_available"],
        timestamp_utc=datetime.now(timezone.utc).isoformat()
    )

def get_service_metadata() -> MetadataResponse:
    """Returns verified model metadata and architectural specifications."""
    raw_meta = model_loader.get_metadata()
    feature_order = raw_meta.get("feature_order", [
        "T2M", "PRECTOTCORR", "RH2M", "WS10M", "latitude", "longitude", "month_sin", "month_cos"
    ])
    feature_units = raw_meta.get("feature_units", {
        "T2M": "°C",
        "PRECTOTCORR": "mm/day",
        "RH2M": "%",
        "WS10M": "m/s",
        "latitude": "degrees",
        "longitude": "degrees",
        "month_sin": "unitless",
        "month_cos": "unitless"
    })
    
    return MetadataResponse(
        model_name="Original MLP Reference Model",
        model_type="Multi-Layer Perceptron (Reference Baseline)",
        status="Experimental Reference Model (Not Operational Forecasting)",
        architecture=ArchitectureSpec(
            input_features=8,
            hidden_units=32,
            hidden_activation="ReLU",
            dropout=0.2,
            output_features=1,
            output_type="Standardized target regression with fold inverse transform"
        ),
        feature_order=feature_order,
        feature_units=feature_units,
        target={
            "name": "methane_concentration",
            "unit": "ppb",
            "observation_source": "Sentinel-5P TROPOMI Level-2 Total Column",
            "inverse_transform": "prediction_ppb = prediction_scaled * target_std + target_mean"
        },
        checkpoints_count=15,
        supported_folds=[1, 2, 3],
        supported_seeds=[7, 21, 42, 77, 123],
        scientific_limitations=SCIENTIFIC_LIMITATIONS,
        benchmark_comparison=BENCHMARK_COMPARISON,
        version="1.0.0-reference"
    )
