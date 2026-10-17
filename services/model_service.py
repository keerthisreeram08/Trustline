
from pathlib import Path
import joblib
import numpy as np
import torch
import torch.nn as nn

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "trustline_model.pth"
SCALER_PATH = PROJECT_ROOT / "models" / "trustline_scaler.pkl"

class TrustlineMLP(nn.Sequential):
    def __init__(self):
        super().__init__(
            nn.Linear(32, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 2),
        )

def load_model_and_scaler():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    if not SCALER_PATH.exists():
        raise FileNotFoundError(f"Scaler file not found: {SCALER_PATH}")

    model = TrustlineMLP()
    state_dict = torch.load(
        MODEL_PATH,
        map_location="cpu",
        weights_only=True,
    )
    model.load_state_dict(state_dict)
    model.eval()

    scaler = joblib.load(SCALER_PATH)
    if getattr(scaler, "n_features_in_", None) != 32:
        raise ValueError("The scaler must expect exactly 32 features.")

    return model, scaler

def predict_from_features(features, model, scaler):
    values = np.asarray(features, dtype=np.float32)
    if values.ndim == 1:
        values = values.reshape(1, -1)
    if values.ndim != 2 or values.shape[1] != 32:
        raise ValueError("Expected exactly 32 features per row.")

    scaled_values = scaler.transform(values).astype(np.float32)
    tensor = torch.tensor(scaled_values, dtype=torch.float32)

    with torch.no_grad():
        probabilities = torch.softmax(model(tensor), dim=1).numpy()

    return probabilities
