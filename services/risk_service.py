
from services.model_service import predict_from_features
from services.data_service import validate_features

def get_model_probabilities(features, model, scaler):
    """Validate features and return the model's two class probabilities."""
    values = validate_features(features)
    probabilities = predict_from_features(values, model, scaler)

    if probabilities.shape != (1, 2):
        raise ValueError("The model must return two class probabilities.")

    return {
        "class_0_probability": float(probabilities[0, 0]),
        "class_1_probability": float(probabilities[0, 1]),
        "notice": (
            "These are model class probabilities, not a validated "
            "real-world e-commerce fraud score."
        ),
    }
