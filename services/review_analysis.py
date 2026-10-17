
from collections import Counter
from difflib import SequenceMatcher
import re


def clean_review(text):
    """Normalize review text for comparison."""
    text = str(text).lower().strip()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compare_reviews(review_a, review_b):
    """Return a similarity score between two reviews."""
    a = clean_review(review_a)
    b = clean_review(review_b)

    if not a or not b:
        return 0.0

    return round(SequenceMatcher(None, a, b).ratio(), 4)


def find_similar_reviews(reviews, threshold=0.80):
    """
    Find pairs of reviews whose text similarity meets the threshold.
    Returns review indexes, similarity scores, and original text.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1.")

    results = []
    cleaned = [clean_review(review) for review in reviews]

    for i in range(len(reviews)):
        if not cleaned[i]:
            continue

        for j in range(i + 1, len(reviews)):
            if not cleaned[j]:
                continue

            score = SequenceMatcher(
                None, cleaned[i], cleaned[j]
            ).ratio()

            if score >= threshold:
                results.append({
                    "review_a_index": i,
                    "review_b_index": j,
                    "similarity": round(score, 4),
                    "review_a": str(reviews[i]),
                    "review_b": str(reviews[j]),
                })

    return sorted(
        results,
        key=lambda item: item["similarity"],
        reverse=True,
    )


def review_summary(reviews, threshold=0.80):
    """Summarize review similarity signals without declaring fraud."""
    reviews = [str(review).strip() for review in reviews if str(review).strip()]
    pairs = find_similar_reviews(reviews, threshold)

    normalized = [clean_review(review) for review in reviews]
    repeated_counts = Counter(normalized)
    repeated_groups = [
        {
            "normalized_review": text,
            "count": count,
        }
        for text, count in repeated_counts.items()
        if text and count > 1
    ]

    return {
        "total_reviews": len(reviews),
        "similar_pair_count": len(pairs),
        "repeated_text_groups": repeated_groups,
        "similar_pairs": pairs,
        "threshold": threshold,
        "notice": (
            "Text similarity is a screening signal, not proof of fake reviews."
        ),
    }
