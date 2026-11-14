"""FastAPI application entrypoint for Earth Systems Trend Detective ML Inference Service."""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .schemas import (
    PredictRequest,
    BatchPredictRequest,
    PredictResponse,
    BatchPredictResponse,
    HealthResponse,
    MetadataResponse
)
from .health import check_service_health, get_service_metadata
from .inference_service import run_single_prediction, run_batch_prediction

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("model-service.main")

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description=(
        "Production-grade ML inference microservice for Earth Systems Trend Detective "
        "(NASA Space Apps Challenge 2026). Wraps the 15 production reference MLP checkpoints "
        "across 3 cross-validation folds and 5 seeds."
    )
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verifies service-to-service API key if configured."""
    required_key = settings.MODEL_SERVICE_API_KEY
    if required_key and x_api_key != required_key:
        logger.warning("Unauthorized access attempt: invalid or missing X-API-Key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header"
        )
    return True

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Formats validation errors into clean structured JSON."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "status": "invalid_input"
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Formats value and domain errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "detail": str(exc),
            "status": "invalid_parameter"
        }
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    """Formats missing checkpoint or asset errors."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Asset Unavailable",
            "detail": str(exc),
            "status": "checkpoint_missing"
        }
    )

@app.get("/", tags=["General"])
def root():
    """Root info endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "metadata": "/metadata",
            "predict": "/predict",
            "predict_batch": "/predict/batch"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Diagnostics"])
def get_health():
    """Healthcheck endpoint returning PyTorch environment and checkpoint inventory."""
    return check_service_health()

@app.get("/metadata", response_model=MetadataResponse, tags=["Metadata"])
def get_metadata():
    """Returns verified model architecture, features, units, and scientific limitations."""
    return get_service_metadata()

@app.post("/predict", response_model=PredictResponse, tags=["Inference"], dependencies=[Depends(verify_api_key)])
def predict_single(request: PredictRequest):
    """
    Executes single-sample PyTorch forward pass on CPU.
    Validates the exact 8-feature order, applies fold-specific standardization,
    and returns denormalized atmospheric methane in ppb.
    """
    try:
        return run_single_prediction(request)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(fe))
    except Exception as e:
        logger.error(f"Inference error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference pipeline error: {str(e)}")

@app.post("/predict/batch", response_model=BatchPredictResponse, tags=["Inference"], dependencies=[Depends(verify_api_key)])
def predict_batch(request: BatchPredictRequest):
    """
    Executes vectorized batch inference for up to 1000 samples.
    """
    try:
        return run_batch_prediction(request)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(fe))
    except Exception as e:
        logger.error(f"Batch inference error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Batch inference error: {str(e)}")
