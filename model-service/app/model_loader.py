"""Model loader and cache manager for the 15 PyTorch checkpoints."""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, Any

from .config import settings

logger = logging.getLogger("model-service.loader")

class ModelLoader:
    def __init__(self):
        self.package_dir = Path(settings.MODEL_PACKAGE_DIR).resolve()
        self.device = settings.INFERENCE_DEVICE
        self._predictors: Dict[Tuple[int, int], Any] = {}
        self._metadata: Optional[Dict[str, Any]] = None
        self._ensure_predictor_on_path()

    def _ensure_predictor_on_path(self):
        """Ensures the production reference inference directory is on sys.path."""
        inference_dir = self.package_dir / "inference"
        if inference_dir.exists() and str(inference_dir) not in sys.path:
            sys.path.insert(0, str(inference_dir))

    def get_metadata(self) -> Dict[str, Any]:
        """Loads and returns preprocessing metadata."""
        if self._metadata is None:
            meta_path = self.package_dir / "metadata" / "preprocessing_metadata.json"
            if not meta_path.exists():
                raise FileNotFoundError(f"Preprocessing metadata not found at: {meta_path}")
            with open(meta_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        return self._metadata

    def get_model_config(self) -> Dict[str, Any]:
        """Loads and returns model configuration."""
        cfg_path = self.package_dir / "metadata" / "model_config.json"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_predictor(self, fold: int, seed: int):
        """Retrieves or lazily initializes a cached MethanePredictor instance."""
        key = (int(fold), int(seed))
        if key not in self._predictors:
            self._ensure_predictor_on_path()
            try:
                from predictor import MethanePredictor
            except ImportError:
                # Direct file import fallback
                import importlib.util
                pred_path = self.package_dir / "inference" / "predictor.py"
                if not pred_path.exists():
                    raise FileNotFoundError(f"predictor.py not found at: {pred_path}")
                spec = importlib.util.spec_from_file_location("ref_predictor", str(pred_path))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                MethanePredictor = mod.MethanePredictor

            checkpoint_file = self.package_dir / "checkpoints" / f"fold_{fold}_MLP_seed_{seed}.pt"
            if not checkpoint_file.exists():
                raise FileNotFoundError(f"Checkpoint file does not exist: {checkpoint_file}")

            predictor = MethanePredictor(
                package_dir=self.package_dir,
                fold=fold,
                seed=seed,
                device=self.device
            )
            self._predictors[key] = predictor
            logger.info(f"Loaded and cached MethanePredictor for fold={fold}, seed={seed} on {self.device}")

        return self._predictors[key]

    def scan_checkpoints(self) -> Dict[str, Any]:
        """Verifies the availability of all 15 checkpoints on disk."""
        checkpoints_dir = self.package_dir / "checkpoints"
        available = []
        missing = []
        
        for fold in [1, 2, 3]:
            for seed in [7, 21, 42, 77, 123]:
                fname = f"fold_{fold}_MLP_seed_{seed}.pt"
                fpath = checkpoints_dir / fname
                if fpath.exists() and fpath.stat().st_size > 0:
                    available.append({"fold": fold, "seed": seed, "filename": fname, "size_bytes": fpath.stat().st_size})
                else:
                    missing.append({"fold": fold, "seed": seed, "filename": fname})

        return {
            "total_expected": 15,
            "total_found": len(available),
            "all_available": len(available) == 15,
            "available_checkpoints": available,
            "missing_checkpoints": missing,
            "package_dir": str(self.package_dir)
        }

model_loader = ModelLoader()
