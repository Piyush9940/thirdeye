
from pathlib import Path
import json
import torch
import torch.nn as nn
import numpy as np


class MLP(nn.Module):

    def __init__(self, input_dim=8, hidden_units=32, dropout=0.2):
        super().__init__()

        self.layers = nn.Sequential(
            nn.Linear(input_dim, hidden_units),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_units, 1)
        )

    def forward(self, x):
        return self.layers(x)


class MethanePredictor:

    def __init__(self, package_dir, fold, seed=42, device=None):

        self.package_dir = Path(package_dir)
        self.fold = int(fold)
        self.seed = int(seed)

        if self.fold not in [1, 2, 3]:
            raise ValueError("Fold must be 1, 2, or 3.")

        if self.seed not in [7, 21, 42, 77, 123]:
            raise ValueError("Unsupported checkpoint seed.")

        self.device = torch.device(
            device if device is not None
            else ("cuda" if torch.cuda.is_available() else "cpu")
        )

        metadata_path = (
            self.package_dir
            / "metadata"
            / "preprocessing_metadata.json"
        )

        with open(metadata_path, "r", encoding="utf-8") as file:
            metadata = json.load(file)

        self.feature_order = metadata["feature_order"]

        fold_metadata = metadata["folds"][str(self.fold)]

        self.feature_mean = np.asarray(
            fold_metadata["feature_mean"],
            dtype=np.float32
        )

        self.feature_std = np.asarray(
            fold_metadata["feature_std"],
            dtype=np.float32
        )

        self.target_mean = float(fold_metadata["target_mean"])
        self.target_std = float(fold_metadata["target_std"])

        self.scaled_indices = fold_metadata[
            "scaled_feature_indices"
        ]

        self.month_indices = fold_metadata[
            "month_feature_indices"
        ]

        checkpoint_path = (
            self.package_dir
            / "checkpoints"
            / f"fold_{self.fold}_MLP_seed_{self.seed}.pt"
        )

        checkpoint = torch.load(
            checkpoint_path,
            map_location="cpu",
            weights_only=True
        )

        self.model = MLP(
            input_dim=8,
            hidden_units=int(checkpoint["hidden_units"]),
            dropout=float(checkpoint["dropout"])
        )

        self.model.load_state_dict(
            checkpoint["model_state_dict"],
            strict=True
        )

        self.model.to(self.device)
        self.model.eval()

    def preprocess(self, features):

        values = np.asarray(features, dtype=np.float32)

        if values.shape[-1] != 8:
            raise ValueError(
                "Expected exactly 8 features in this order: "
                + ", ".join(self.feature_order)
            )

        if not np.all(np.isfinite(values)):
            raise ValueError("Input features must all be finite.")

        original_shape = values.shape
        values = values.reshape(-1, 8).copy()

        values[:, self.scaled_indices] = (
            values[:, self.scaled_indices] - self.feature_mean
        ) / self.feature_std

        return values.reshape(original_shape)

    def predict(self, features):

        raw = np.asarray(features, dtype=np.float32)

        if raw.ndim == 1:
            raw = raw.reshape(1, -1)

        scaled = self.preprocess(raw)

        tensor = torch.as_tensor(
            scaled,
            dtype=torch.float32,
            device=self.device
        )

        with torch.no_grad():
            prediction_scaled = (
                self.model(tensor)
                .cpu()
                .numpy()
                .reshape(-1)
            )

        prediction_ppb = (
            prediction_scaled * self.target_std
            + self.target_mean
        )

        return {
            "model": "Original MLP Reference Model",
            "fold": self.fold,
            "seed": self.seed,
            "prediction_ppb": prediction_ppb.tolist(),
            "unit": "ppb",
            "status": "experimental_reference",
            "scientific_warning": (
                "Not validated for operational methane forecasting. "
                "Interpret within the original pilot-data scope."
            )
        }
