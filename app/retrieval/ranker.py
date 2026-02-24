from difflib import SequenceMatcher
from typing import Optional

# Field weights using ACTUAL CSV column names
FIELD_WEIGHTS = {
    "industry":        0.30,
    "geography":       0.20,
    "methodology":     0.20,
    "tags":            0.15,   # CSV column is 'tags' (not 'keywords')
    "year":            0.05,
    "client_category": 0.10,   # CSV column is 'client_category' (not 'client_type')
}


def _fuzzy_score(value: str, target: str) -> float:
    if not value or not target:
        return 0.0
    return SequenceMatcher(None, str(value).lower().strip(), str(target).lower().strip()).ratio()


def _field_match_score(row_value: str, filter_value: str) -> float:
    row_val = str(row_value).lower().strip()
    flt_val = str(filter_value).lower().strip()

    if not row_val or not flt_val or row_val == "nan":
        return 0.0
    if flt_val == row_val:
        return 1.0
    if flt_val in row_val or row_val in flt_val:
        return 0.8
    return _fuzzy_score(row_val, flt_val)


def rank_candidates(
    candidates: list[dict],
    filters: dict,
    top_k: int = 3,
    min_score: Optional[float] = 0.0,
) -> list[dict]:
    """
    Re-ranks candidates using weighted field scoring.
    Expects filters to use actual CSV column names (post-mapping).
    """
    if not candidates:
        return []

    scored = []
    for row in candidates:
        total_score = 0.0
        score_breakdown = {}

        for field, weight in FIELD_WEIGHTS.items():
            filter_val = filters.get(field)
            if not filter_val:
                continue
            row_val = row.get(field, "")
            field_score = _field_match_score(str(row_val), str(filter_val))
            weighted = field_score * weight
            score_breakdown[field] = round(weighted, 4)
            total_score += weighted

        row["_rank_score"] = round(total_score, 4)
        row["_score_breakdown"] = score_breakdown
        scored.append(row)

    scored.sort(key=lambda x: x["_rank_score"], reverse=True)

    if min_score is not None:
        scored = [r for r in scored if r["_rank_score"] >= min_score]

    return scored[:top_k]


def log_ranking(ranked: list[dict]) -> None:
    print(f"\n{'Rank':<6}{'File':<45}{'Score':<10}Breakdown")
    print("-" * 85)
    for i, row in enumerate(ranked, 1):
        fname = str(row.get("file_name", "unknown"))[:43]
        score = row.get("_rank_score", 0)
        breakdown = row.get("_score_breakdown", {})
        print(f"{i:<6}{fname:<45}{score:<10}{breakdown}")
    print()
