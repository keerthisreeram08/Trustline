import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from services.data_service import append_history, load_history


class HistoryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.history_path = Path(self.temp_directory.name) / "data" / "history.csv"

    def test_load_missing_history_returns_empty_list(self):
        self.assertEqual(load_history(self.history_path), [])

    def test_load_reads_existing_history_csv(self):
        self.history_path.parent.mkdir(parents=True)
        self.history_path.write_text(
            "date,seller,category,reviews,similar_pairs,status,indicator\n"
            "2026-10-17 15:00,Sample Shop,Electronics,3,1,Review recommended,42\n",
            encoding="utf-8",
        )

        records = load_history(self.history_path)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["seller"], "Sample Shop")
        self.assertEqual(records[0]["reviews"], 3)
        self.assertEqual(records[0]["indicator"], 42)

    def test_append_persists_before_returning_updated_history(self):
        existing = [{
            "date": "2026-10-16 15:00",
            "seller": "Earlier Shop",
            "category": "Books",
            "reviews": 2,
            "similar_pairs": 0,
            "status": "Insufficient evidence",
            "indicator": 50,
        }]
        new_record = {
            "date": "2026-10-17 15:00",
            "seller": "New Shop",
            "category": "Books",
            "reviews": 1,
            "similar_pairs": 0,
            "status": "Insufficient evidence",
            "indicator": 50,
        }

        updated = append_history(existing, new_record, self.history_path)

        self.assertEqual(existing[0]["seller"], "Earlier Shop")
        self.assertEqual(len(existing), 1)
        self.assertEqual(updated, existing + [new_record])
        self.assertEqual(load_history(self.history_path), updated)
        saved_csv = self.history_path.read_text(encoding="utf-8")
        self.assertNotIn("review_text", saved_csv)

    def test_append_failure_preserves_existing_file_and_input_history(self):
        self.history_path.parent.mkdir(parents=True)
        self.history_path.write_text(
            "date,seller,category,reviews,similar_pairs,status,indicator\n"
            "2026-10-17 15:00,Earlier Shop,Books,2,0,Insufficient evidence,50\n",
            encoding="utf-8",
        )
        original_csv = self.history_path.read_text(encoding="utf-8")
        existing = [{
            "date": "2026-10-16 15:00",
            "seller": "Earlier Shop",
            "category": "Books",
            "reviews": 2,
            "similar_pairs": 0,
            "status": "Insufficient evidence",
            "indicator": 50,
        }]

        with patch("services.data_service.os.replace", side_effect=OSError("disk unavailable")):
            with self.assertRaisesRegex(OSError, "disk unavailable"):
                append_history(existing, {"seller": "New Shop"}, self.history_path)

        self.assertEqual(existing[0]["seller"], "Earlier Shop")
        self.assertEqual(len(existing), 1)
        self.assertEqual(self.history_path.read_text(encoding="utf-8"), original_csv)
        self.assertEqual(
            len(list(self.history_path.parent.glob(f".{self.history_path.name}.*.tmp"))),
            0,
        )

    def test_load_failure_propagates_for_ui_to_report(self):
        self.history_path.parent.mkdir(parents=True)
        self.history_path.write_text("date,seller\ninvalid", encoding="utf-8")
        with patch("services.data_service.pd.read_csv", side_effect=pd.errors.ParserError("invalid CSV")):
            with self.assertRaisesRegex(pd.errors.ParserError, "invalid CSV"):
                load_history(self.history_path)


if __name__ == "__main__":
    unittest.main()
