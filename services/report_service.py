from collections import Counter
from datetime import date, datetime

from services.review_analysis import clean_review


def count_review_comparisons(reviews):
    """Count pairs the analyzer can compare after its text normalization."""
    comparable_review_count = sum(bool(clean_review(review)) for review in reviews)
    return comparable_review_count * (comparable_review_count - 1) // 2


def build_review_report_data(review_result, max_visible_pairs=8):
    """Prepare report counts and a bounded view of the actual flagged pairs."""
    review_count = int(review_result.get("total_reviews", 0))
    possible_pair_count = int(review_result.get(
        "comparison_count", review_count * (review_count - 1) // 2
    ))
    similar_pairs = review_result.get("similar_pairs", [])
    flagged_pair_count = len(similar_pairs)

    pairs = []
    for index, pair in enumerate(similar_pairs, start=1):
        review_a_index = int(pair["review_a_index"])
        review_b_index = int(pair["review_b_index"])
        pairs.append({
            **pair,
            "pair_number": index,
            "label": f"Reviews {review_a_index + 1} & {review_b_index + 1}",
            "exact_duplicate": (
                clean_review(pair["review_a"]) == clean_review(pair["review_b"])
            ),
        })

    return {
        "review_count": review_count,
        "possible_pair_count": possible_pair_count,
        "flagged_pair_count": flagged_pair_count,
        "non_matching_pair_count": max(
            0, possible_pair_count - flagged_pair_count
        ),
        "exact_duplicate_group_count": len(
            review_result.get("repeated_text_groups", [])
        ),
        "threshold": float(review_result.get("threshold", 0.80)),
        "visible_pairs": pairs[:max_visible_pairs],
        "hidden_pair_count": max(0, flagged_pair_count - max_visible_pairs),
    }


def build_indicator_contributions(reasons, unavailable_signals=()):
    """Separate measured heuristic adjustments from unavailable inputs."""
    contributions = []
    for kind, explanation, points in reasons:
        lowered = explanation.lower()
        if "similar review" in lowered or "review pair" in lowered or "reviews are needed" in lowered:
            label = "Review similarity"
        elif "account age" in lowered:
            label = "Account age (entered)"
        elif "rating" in lowered:
            label = "Rating (entered)"
        elif "review count" in lowered:
            label = "Review count (entered)"
        elif "price" in lowered:
            label = "Price comparison (not assessed)"
        else:
            label = kind

        assessed = kind not in {"Missing data", "Not assessed"}
        if not assessed and "(not assessed)" not in label:
            label = label.replace("(entered)", "(not assessed)")
            if "(not assessed)" not in label:
                label = f"{label} (not assessed)"
        contributions.append({
            "signal": label,
            "points": float(points),
            "explanation": explanation,
            "assessed": assessed,
        })

    labels = {item["signal"] for item in contributions}
    for signal in unavailable_signals:
        label = f"{signal} (not assessed)"
        if label not in labels:
            contributions.append({
                "signal": label,
                "points": 0.0,
                "explanation": "No reliable input or comparison source is available.",
                "assessed": False,
            })
            labels.add(label)

    return contributions


def summarize_history(records):
    """Aggregate only fields present in saved history, ignoring unusable dates."""
    statuses = Counter()
    categories = Counter()
    daily_counts = Counter()
    dated_records = 0

    for record in records:
        status = str(record.get("status", "")).strip()
        category = str(record.get("category", "")).strip()
        if status:
            statuses[status] += 1
        if category:
            categories[category] += 1

        raw_date = record.get("date")
        if isinstance(raw_date, datetime):
            parsed_date = raw_date.date()
        elif isinstance(raw_date, date):
            parsed_date = raw_date
        elif raw_date:
            try:
                parsed_date = datetime.fromisoformat(
                    str(raw_date).strip().replace("Z", "+00:00")
                ).date()
            except ValueError:
                continue
        else:
            continue

        daily_counts[parsed_date.isoformat()] += 1
        dated_records += 1

    return {
        "status_counts": dict(statuses),
        "category_counts": dict(categories),
        "daily_counts": [
            {"date": day, "analyses": count}
            for day, count in sorted(daily_counts.items())
        ],
        "dated_record_count": dated_records,
    }
