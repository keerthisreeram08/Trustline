
import os
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

EXPECTED_FEATURES = 32


def load_history(path):
    """Load saved history rows, preserving the existing CSV format."""
    history_path = Path(path)
    if not history_path.exists():
        return []
    return pd.read_csv(history_path).to_dict("records")


def append_history(records, record, path):
    """Persist a new history row before returning the updated in-memory list."""
    updated_records = [*records, record]
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{history_path.name}.",
            suffix=".tmp",
            dir=history_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        pd.DataFrame(updated_records).to_csv(temporary_path, index=False)
        os.replace(temporary_path, history_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise

    return updated_records


def validate_features(features):
    """Validate the 32 numerical features required by the model."""
    try:
        values = np.asarray(features, dtype=np.float32)
    except (TypeError, ValueError):
        raise ValueError("All 32 features must be numerical values.")

    if values.ndim != 1 or values.size != EXPECTED_FEATURES:
        raise ValueError("Exactly 32 numerical features are required.")

    if not np.isfinite(values).all():
        raise ValueError("Features cannot contain NaN or infinite values.")

    return values
