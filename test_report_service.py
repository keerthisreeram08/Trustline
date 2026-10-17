import unittest

from services.report_service import (
    build_indicator_contributions,
    build_review_report_data,
    count_review_comparisons,
    summarize_history,
)
from services.review_analysis import review_summary


class ReviewReportDataTests(unittest.TestCase):
    def test_empty_and_single_review_inputs_have_no_comparisons(self):
        for result in (review_summary([]), review_summary(["One review"])):
            with self.subTest(review_count=result["total_reviews"]):
                report = build_review_report_data(result)
                self.assertEqual(report["possible_pair_count"], 0)
                self.assertEqual(report["flagged_pair_count"], 0)
                self.assertEqual(report["non_matching_pair_count"], 0)
                self.assertEqual(report["visible_pairs"], [])

    def test_pair_counts_and_exact_duplicate_evidence_use_actual_reviews(self):
        result = review_summary(["Loved this item!", "LOVED THIS ITEM.", "Poor quality"])
        result["comparison_count"] = count_review_comparisons(
            ["Loved this item!", "LOVED THIS ITEM.", "Poor quality"]
        )

        report = build_review_report_data(result)

        self.assertEqual(report["review_count"], 3)
        self.assertEqual(report["possible_pair_count"], 3)
        self.assertEqual(report["flagged_pair_count"], 1)
        self.assertEqual(report["non_matching_pair_count"], 2)
        self.assertEqual(report["exact_duplicate_group_count"], 1)
        self.assertEqual(report["visible_pairs"][0]["label"], "Reviews 1 & 2")
        self.assertTrue(report["visible_pairs"][0]["exact_duplicate"])
        self.assertEqual(report["threshold"], 0.80)

    def test_comparison_count_excludes_reviews_empty_after_normalization(self):
        reviews = ["!!!", "Useful item", "Useful item!"]
        result = review_summary(reviews)
        result["comparison_count"] = count_review_comparisons(reviews)

        report = build_review_report_data(result)

        self.assertEqual(report["review_count"], 3)
        self.assertEqual(report["possible_pair_count"], 1)
        self.assertEqual(report["flagged_pair_count"], 1)
        self.assertEqual(report["non_matching_pair_count"], 0)

    def test_evidence_display_is_capped_and_reports_hidden_pair_count(self):
        pairs = [
            {
                "review_a_index": index,
                "review_b_index": index + 1,
                "similarity": 0.9,
                "review_a": f"Review {index}",
                "review_b": f"Review {index + 1}",
            }
            for index in range(10)
        ]
        result = {
            "total_reviews": 11,
            "similar_pairs": pairs,
            "repeated_text_groups": [],
            "threshold": 0.80,
        }

        report = build_review_report_data(result)

        self.assertEqual(len(report["visible_pairs"]), 8)
        self.assertEqual(report["hidden_pair_count"], 2)
        self.assertEqual(report["flagged_pair_count"], 10)


class IndicatorContributionTests(unittest.TestCase):
    def test_chart_contributions_label_provenance_and_keep_documented_points(self):
        reasons = [
            ("Caution", "2 similar review pair(s) were found.", -20.0),
            ("Submitted detail", "Account age entered as 365 days.", 4.0),
            ("Not assessed", "Price was entered, but no reliable market-price comparison is connected.", 0),
        ]

        contributions = build_indicator_contributions(reasons)

        self.assertEqual(
            [item["signal"] for item in contributions],
            [
                "Review similarity",
                "Account age (entered)",
                "Price comparison (not assessed)",
            ],
        )
        self.assertEqual([item["points"] for item in contributions], [-20.0, 4.0, 0.0])
        self.assertEqual(
            [item["assessed"] for item in contributions],
            [True, True, False],
        )

    def test_missing_inputs_are_not_assessed_instead_of_zero_contributions(self):
        contributions = build_indicator_contributions([
            ("Missing data", "Account age was not provided.", 0),
            ("Missing data", "Average rating was not provided.", 0),
            ("Not assessed", "Price was entered, but no comparison is connected.", 0),
        ])

        self.assertEqual(
            [item["signal"] for item in contributions],
            [
                "Account age (not assessed)",
                "Rating (not assessed)",
                "Price comparison (not assessed)",
            ],
        )
        self.assertTrue(all(not item["assessed"] for item in contributions))


class HistorySummaryTests(unittest.TestCase):
    def test_status_category_and_dates_are_aggregated_from_saved_records(self):
        records = [
            {
                "date": "2026-10-17 15:00",
                "category": "Electronics",
                "status": "Review recommended",
            },
            {
                "date": "2026-10-17T18:30:00",
                "category": "Electronics",
                "status": "Review recommended",
            },
            {
                "date": "2026-10-18",
                "category": "Books",
                "status": "Insufficient evidence",
            },
        ]

        summary = summarize_history(records)

        self.assertEqual(summary["status_counts"], {
            "Review recommended": 2,
            "Insufficient evidence": 1,
        })
        self.assertEqual(summary["category_counts"], {
            "Electronics": 2,
            "Books": 1,
        })
        self.assertEqual(summary["daily_counts"], [
            {"date": "2026-10-17", "analyses": 2},
            {"date": "2026-10-18", "analyses": 1},
        ])
        self.assertEqual(summary["dated_record_count"], 3)

    def test_legacy_missing_fields_and_unusable_dates_do_not_create_fake_values(self):
        summary = summarize_history([
            {"category": "Fashion"},
            {"date": "not-a-date", "status": "Review recommended"},
            {"date": "2026-10-17", "category": "", "status": ""},
        ])

        self.assertEqual(summary["category_counts"], {"Fashion": 1})
        self.assertEqual(summary["status_counts"], {"Review recommended": 1})
        self.assertEqual(summary["daily_counts"], [
            {"date": "2026-10-17", "analyses": 1},
        ])
        self.assertEqual(summary["dated_record_count"], 1)


if __name__ == "__main__":
    unittest.main()
