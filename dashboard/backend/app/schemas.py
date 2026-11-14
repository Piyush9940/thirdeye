"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Pydantic Request & Response Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TimePoint(BaseModel):
    date: str
    value: float

class LinearRegressionStats(BaseModel):
    slope: float = Field(..., description="Slope per month")
    annualized_rate: float = Field(..., description="Annualized rate of change")
    unit: str
    intercept: float
    r_squared: float
    std_err: float
    p_value: float
    ci_lower: float
    ci_upper: float

class MannKendallStats(BaseModel):
    tau: float = Field(..., description="Kendall's rank correlation coefficient")
    p_value: float
    s_statistic: float
    z_score: Optional[float] = None
    is_significant: bool
    trend_direction: str

class SensSlopeStats(BaseModel):
    slope: float = Field(..., description="Theil-Sen robust slope per month")
    annualized_rate: float
    unit: str
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None

class TrendAnalysisRequest(BaseModel):
    variable: str = Field(default="T2M", description="Environmental variable (T2M, PRECTOTCORR, RH2M, WS10M, CH4)")
    region: Optional[str] = Field(default="All_India", description="Geographical zone or 'All_India'")
    node_id: Optional[str] = Field(default=None, description="Specific spatial node ID e.g. '10_0'")
    start_date: Optional[str] = Field(default="2015-01-01", description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default="2024-12-01", description="End date YYYY-MM-DD")
    aggregation: Optional[str] = Field(default="monthly", description="'monthly' or 'annual'")
    remove_seasonality: Optional[bool] = Field(default=False, description="Apply seasonal difference")

class TrendAnalysisResponse(BaseModel):
    success: bool
    variable: str
    variable_name: str
    unit: str
    region: str
    node_id: Optional[str] = None
    start_date: str
    end_date: str
    sample_size: int
    missing_count: int
    time_series: List[TimePoint]
    linear_regression: LinearRegressionStats
    mann_kendall: MannKendallStats
    sens_slope: SensSlopeStats
    trend_classification: str
    significance_level: float = 0.05
    is_statistically_significant: bool
    plain_language_summary: str
    scientific_caveats: List[str]

class RegionalComparisonRequest(BaseModel):
    variable: str = Field(default="T2M", description="Environmental variable")
    start_date: Optional[str] = Field(default="2015-01-01")
    end_date: Optional[str] = Field(default="2024-12-01")
    aggregation: Optional[str] = Field(default="monthly")

class RegionalComparisonItem(BaseModel):
    region_id: str
    region_name: str
    total_nodes: int
    observation_count: int
    mean_value: float
    annual_rate_of_change: float
    trend_direction: str
    p_value: float
    is_significant: bool
    sens_slope_annual: float

class RegionalComparisonResponse(BaseModel):
    success: bool
    variable: str
    variable_name: str
    unit: str
    start_date: str
    end_date: str
    regions: List[RegionalComparisonItem]
    interpretation: str

class AIQueryRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None
    provider: Optional[str] = "gemini"

class AIQueryResponse(BaseModel):
    success: bool
    question: str
    provider_used: str
    answer: str
    grounded_evidence: Dict[str, Any]

class LiveInferenceRequest(BaseModel):
    features: List[float] = Field(..., description="8 numerical features [T2M, PRECTOTCORR, RH2M, WS10M, lat, lon, month_sin, month_cos]")
    fold: int = 1
    seed: int = 42

class LiveInferenceResponse(BaseModel):
    success: bool
    model: str
    fold: int
    seed: int
    predicted_ch4_ppb: float
    unit: str = "ppb"
    status: str = "experimental_reference"
    warning: str
