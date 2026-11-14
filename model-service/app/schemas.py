"""Pydantic data schemas for request validation and response formatting."""

import math
from typing import Union, Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

VALID_FOLDS = [1, 2, 3]
VALID_SEEDS = [7, 21, 42, 77, 123]
FEATURE_ORDER = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "latitude",
    "longitude",
    "month_sin",
    "month_cos"
]

class FeatureDict(BaseModel):
    T2M: float = Field(..., description="Air Temperature at 2m (in °C or K)")
    PRECTOTCORR: float = Field(..., description="Precipitation rate (mm/day)")
    RH2M: float = Field(..., description="Relative Humidity at 2m (%)")
    WS10M: float = Field(..., description="Wind Speed at 10m (m/s)")
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    month_sin: Optional[float] = Field(None, description="Cyclical month sine encoding sin(2*pi*m/12)")
    month_cos: Optional[float] = Field(None, description="Cyclical month cosine encoding cos(2*pi*m/12)")
    month: Optional[int] = Field(None, ge=1, le=12, description="Calendar month (1-12) used to derive month_sin/month_cos")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases_and_derivation(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        # Handle field aliases
        if "lat" in d and "latitude" not in d:
            d["latitude"] = d["lat"]
        if "lon" in d and "longitude" not in d:
            d["longitude"] = d["lon"]
        if "sin_month" in d and "month_sin" not in d:
            d["month_sin"] = d["sin_month"]
        if "cos_month" in d and "month_cos" not in d:
            d["month_cos"] = d["cos_month"]
        
        # Derive cyclical month encodings if calendar month is given
        if d.get("month") is not None and (d.get("month_sin") is None or d.get("month_cos") is None):
            m = int(d["month"])
            angle = 2.0 * math.pi * (m / 12.0)
            if d.get("month_sin") is None:
                d["month_sin"] = math.sin(angle)
            if d.get("month_cos") is None:
                d["month_cos"] = math.cos(angle)
                
        # Default to neutral mid-year if completely omitted
        if d.get("month_sin") is None:
            d["month_sin"] = 0.5
        if d.get("month_cos") is None:
            d["month_cos"] = 0.866
            
        return d

    @field_validator("T2M", "PRECTOTCORR", "RH2M", "WS10M", "latitude", "longitude", "month_sin", "month_cos")
    @classmethod
    def validate_finite(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("Input feature values must be finite numbers (no NaN or Inf).")
        return v

    def to_ordered_list(self) -> List[float]:
        return [
            float(self.T2M),
            float(self.PRECTOTCORR),
            float(self.RH2M),
            float(self.WS10M),
            float(self.latitude),
            float(self.longitude),
            float(self.month_sin),
            float(self.month_cos)
        ]


class PredictRequest(BaseModel):
    fold: int = Field(default=1, description="Cross-validation fold index (1, 2, or 3)")
    seed: int = Field(default=42, description="Random seed checkpoint (7, 21, 42, 77, 123)")
    features: Union[FeatureDict, List[float]] = Field(..., description="Input feature dictionary or exact 8-element list")

    @field_validator("fold")
    @classmethod
    def validate_fold(cls, v: int) -> int:
        if v not in VALID_FOLDS:
            raise ValueError(f"Fold must be one of {VALID_FOLDS}. Received: {v}")
        return v

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, v: int) -> int:
        if v not in VALID_SEEDS:
            raise ValueError(f"Seed must be one of {VALID_SEEDS}. Received: {v}")
        return v

    @field_validator("features")
    @classmethod
    def validate_features_list(cls, v: Union[FeatureDict, List[float]]) -> Union[FeatureDict, List[float]]:
        if isinstance(v, list):
            if len(v) != 8:
                raise ValueError(
                    f"Expected exactly 8 features in order {FEATURE_ORDER}. Received list of length {len(v)}."
                )
            for i, val in enumerate(v):
                if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Feature at index {i} ({FEATURE_ORDER[i]}) must be a finite number.")
        return v


class BatchPredictRequest(BaseModel):
    fold: int = Field(default=1, description="Cross-validation fold index (1, 2, or 3)")
    seed: int = Field(default=42, description="Random seed checkpoint (7, 21, 42, 77, 123)")
    items: List[Union[FeatureDict, List[float]]] = Field(..., description="List of feature dictionaries or 8-element lists")

    @field_validator("fold")
    @classmethod
    def validate_fold(cls, v: int) -> int:
        if v not in VALID_FOLDS:
            raise ValueError(f"Fold must be one of {VALID_FOLDS}. Received: {v}")
        return v

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, v: int) -> int:
        if v not in VALID_SEEDS:
            raise ValueError(f"Seed must be one of {VALID_SEEDS}. Received: {v}")
        return v

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: List[Any]) -> List[Any]:
        if not v or len(v) == 0:
            raise ValueError("Batch items array cannot be empty.")
        if len(v) > 1000:
            raise ValueError("Batch limit exceeded: maximum 1000 items per request.")
        return v


class PredictResponse(BaseModel):
    prediction_ppb: float
    output_unit: str = "ppb"
    model: str = "Original MLP Reference Model"
    fold: int
    seed: int
    status: str = "experimental_reference"
    input_features: Dict[str, float]
    scientific_warning: str
    scientific_disclosure: str


class BatchPredictResponse(BaseModel):
    count: int
    predictions_ppb: List[float]
    fold: int
    seed: int
    output_unit: str = "ppb"
    status: str = "experimental_reference"
    scientific_warning: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    python_version: str
    pytorch_version: str
    device: str
    checkpoints_found: int
    checkpoints_expected: int = 15
    all_checkpoints_loaded: bool
    timestamp_utc: str


class ArchitectureSpec(BaseModel):
    input_features: int = 8
    hidden_units: int = 32
    hidden_activation: str = "ReLU"
    dropout: float = 0.2
    output_features: int = 1
    output_type: str = "Normalized methane regression"


class MetadataResponse(BaseModel):
    model_name: str
    model_type: str
    status: str
    architecture: ArchitectureSpec
    feature_order: List[str]
    feature_units: Dict[str, str]
    target: Dict[str, Any]
    checkpoints_count: int
    supported_folds: List[int]
    supported_seeds: List[int]
    scientific_limitations: List[str]
    benchmark_comparison: List[Dict[str, Any]]
    version: str
