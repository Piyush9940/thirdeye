# Model Architecture Specification

## Input Preprocessing & Standardization
Features 0 through 5 are standardized according to the fold-specific training distribution:
$$x' = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}}}$$

Features 6 and 7 (Month Sine and Month Cosine) encode periodic calendar time:
$$\text{month\_sin} = \sin\left(\frac{2\pi (m - 1)}{12}\right)$$
$$\text{month\_cos} = \cos\left(\frac{2\pi (m - 1)}{12}\right)$$

## PyTorch Model Definition
```python
import torch.nn as nn

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
```

## Target De-Normalization
Predicted outputs are scaled back to parts-per-billion (ppb):
$$\hat{y}_{\text{ppb}} = \hat{y}_{\text{scaled}} \cdot \sigma_{y,\text{train}} + \mu_{y,\text{train}}$$
