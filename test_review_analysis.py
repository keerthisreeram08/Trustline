import unittest

from services.review_analysis import compare_reviews, find_similar_reviews, review_summary


class ReviewAnalysisTests(unittest.TestCase):
    def test_normalization_ignores_case_punctuation_urls_and_extra_whitespace(self):
        first = "  AMAZING!!!  Visit https://example.com/item now. "
        second = "amazing visit now"

        self.assertEqual(compare_reviews(first, second), 1.0)
        self.assertEqual(compare_reviews("   ", second), 0.0)

    def test_blank_reviews_are_excluded_from_summary(self):
        result = review_summary(["", "  \t\n", "A useful product"])

        self.assertEqual(result["total_reviews"], 1)
        self.assertEqual(result["similar_pair_count"], 0)
        self.assertEqual(result["repeated_text_groups"], [])
        self.assertEqual(result["similar_pairs"], [])

    def test_exact_duplicates_group_after_normalization(self):
        result = review_summary(
            ["Loved this item!", "  LOVED this item.  ", "", "Different product"]
        )

        self.assertEqual(result["repeated_text_groups"], [
            {"normalized_review": "loved this item", "count": 2}
        ])
        self.assertEqual(result["total_reviews"], 3)
        self.assertEqual(result["similar_pair_count"], 1)

    def test_threshold_includes_equal_score_and_excludes_higher_threshold(self):
        reviews = ["abc", "ab"]

        # SequenceMatcher gives this pair a deterministic similarity of exactly 0.8.
        self.assertEqual(find_similar_reviews(reviews, threshold=0.79)[0]["similarity"], 0.8)
        self.assertEqual(find_similar_reviews(reviews, threshold=0.80)[0]["similarity"], 0.8)
        self.assertEqual(find_similar_reviews(reviews, threshold=0.81), [])

    def test_empty_input_and_single_review_have_no_pairs(self):
        empty = review_summary([])
        single = review_summary(["One review"])

        self.assertEqual(empty["total_reviews"], 0)
        self.assertEqual(empty["similar_pair_count"], 0)
        self.assertEqual(empty["similar_pairs"], [])
        self.assertEqual(single["total_reviews"], 1)
        self.assertEqual(single["similar_pair_count"], 0)
        self.assertEqual(single["similar_pairs"], [])

    def test_small_input_reports_expected_pair_indexes_and_count(self):
        pairs = find_similar_reviews(["abc", "ab", "xyz"], threshold=0.80)

        self.assertEqual(len(pairs), 1)
        self.assertEqual(
            (pairs[0]["review_a_index"], pairs[0]["review_b_index"]),
            (0, 1),
        )
        self.assertEqual(pairs[0]["similarity"], 0.8)

    def test_threshold_outside_supported_range_is_rejected(self):
        for threshold in (-0.01, 1.01):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    find_similar_reviews(["same", "same"], threshold=threshold)


if __name__ == "__main__":
    unittest.main()
