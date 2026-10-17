
import unittest

from services.model_service import load_model_and_scaler, predict_from_features
import numpy as np


class ModelSmokeTests(unittest.TestCase):
    def test_model_and_scaler_load_and_predict(self):
        model, scaler = load_model_and_scaler()
        self.assertEqual(scaler.n_features_in_, 32)

        sample = np.zeros(32, dtype=np.float32)
        probabilities = predict_from_features(sample, model, scaler)

        self.assertEqual(probabilities.shape, (1, 2))
        self.assertTrue(np.isfinite(probabilities).all())


if __name__ == "__main__":
    unittest.main()
