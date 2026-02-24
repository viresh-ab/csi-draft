import re
import pandas as pd
from app.core.config import METADATA_PATH
from app.retrieval.ranker import rank_candidates


BROWSE_ALL_PHRASES = (
    "all case studies",
    "list case studies",
    "list all",
    "show all",
    "all studies",
    "fetch all",
    "get all",
)

# Maps intent classifier filter keys → actual CSV column names
FILTER_COLUMN_MAP = {
    "file_name":   "file_name",
    "industry":    "industry",
    "geography":   "geography",
    "methodology": "methodology",
    "keywords":    "tags",          # intent says 'keywords', CSV has 'tags'
    "tags":        "tags",
    "year":        "year",
    "region":      "geography",
    "location":    "geography",
    "country":     "geography",
    "client_type": "client_category",  # intent says 'client_type', CSV has 'client_category'
    "category":    "client_category",
    "client_category": "client_category",
    "sample_size": "sample_size",
    "sample_sizes": "sample_size",
    "study_type":  "study_type",
    "summary":     "summary",
}


def load_metadata() -> pd.DataFrame:
    """Loads and normalises the metadata CSV."""
    df = pd.read_csv(METADATA_PATH)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _is_browse_all_query(user_query: str | None) -> bool:
    """Heuristic to allow broad retrieval requests like 'list all case studies'."""
    if not user_query:
        return False

    query = str(user_query).lower().strip()
    if "case stud" not in query and "studies" not in query:
        return False

    return any(phrase in query for phrase in BROWSE_ALL_PHRASES)


def _infer_filters_from_query(df: pd.DataFrame, user_query: str | None) -> dict:
    """Fallback extraction for common fields when LLM returns weak/empty filters."""
    if not user_query:
        return {}

    query = str(user_query).lower()
    inferred = {}

    year_match = re.search(r"\b(19|20)\d{2}\b", query)
    if year_match:
        inferred["year"] = year_match.group(0)

    sample_match = re.search(r"(?:sample\s*size|n\s*=?)\s*(\d+)", query)
    if sample_match:
        inferred["sample_size"] = sample_match.group(1)
    elif re.search(r"\b(high|higher|large|larger)\s+sample\s+size\b", query):
        inferred["sample_size"] = "high"

    for col in ["industry", "geography", "client_category", "methodology", "study_type"]:
        if col not in df.columns:
            continue
        values = sorted({str(v).strip() for v in df[col].dropna().tolist() if str(v).strip()})
        for value in values:
            if value.lower() in query:
                inferred[col] = value
                break

    # If the user explicitly references a filename (or a long unique phrase),
    # prioritize exact file-name retrieval.
    if "file_name" in df.columns:
        for file_name in df["file_name"].dropna().astype(str).tolist():
            lowered = file_name.lower()
            if lowered and lowered in query:
                inferred["file_name"] = file_name
                break

    return inferred


def _build_sample_size_match_series(df: pd.DataFrame, value: str, user_query: str | None = None) -> pd.Series:
    """Comparator-aware matching for sample_size (e.g., '>500', 'high sample size')."""
    normalized = str(value).strip().lower()
    numeric = pd.to_numeric(df["sample_size"], errors="coerce")

    comparison_text = f"{normalized} {str(user_query or '').lower()}"

    if re.search(r"\b(high|higher|large|larger)\b", comparison_text):
        threshold = numeric.quantile(0.75)
        if pd.notna(threshold):
            return numeric.ge(threshold).fillna(False)

    comparator_match = re.search(r"(>=|<=|>|<|=)?\s*(\d+)", normalized)
    if comparator_match:
        op = comparator_match.group(1) or "="
        target = float(comparator_match.group(2))
        if op == ">":
            return numeric.gt(target).fillna(False)
        if op == ">=":
            return numeric.ge(target).fillna(False)
        if op == "<":
            return numeric.lt(target).fillna(False)
        if op == "<=":
            return numeric.le(target).fillna(False)
        return numeric.eq(target).fillna(False)

    return df["sample_size"].astype(str).str.lower().str.contains(normalized, na=False, regex=False)


def _build_match_series(df: pd.DataFrame, col: str, value: str, user_query: str | None = None) -> pd.Series:
    """Column-aware matching for better precision on numeric fields."""
    normalized = str(value).strip().lower()

    if col == "sample_size":
        return _build_sample_size_match_series(df, value, user_query=user_query)

    if col == "year":
        numeric = pd.to_numeric(df[col], errors="coerce")
        try:
            target = float(normalized)
            return numeric.eq(target).fillna(False)
        except ValueError:
            return df[col].astype(str).str.lower().str.contains(normalized, na=False, regex=False)

    return df[col].astype(str).str.lower().str.contains(normalized, na=False, regex=False)


def search_metadata(filters: dict, top_k: int = 3, user_query: str | None = None) -> list[dict]:
    """
    Retrieves and ranks case study candidates from the CSV.

    Maps intent classifier filter keys to actual CSV column names,
    scores each row, then passes to ranker for weighted re-ranking.
    """
    df = load_metadata()
    filters = filters or {}

    # For no-filter queries, only return results for explicit browse-all intents.
    if not filters:
        if _is_browse_all_query(user_query):
            return df.to_dict(orient="records")

        filters = _infer_filters_from_query(df, user_query)
        if not filters:
            return []

    scores = pd.Series([0] * len(df), dtype=int)

    # Remap filter keys to actual CSV columns before searching
    mapped_filters = {}
    for key, value in filters.items():
        col = FILTER_COLUMN_MAP.get(key, key)
        if value and col in df.columns:
            mapped_filters[col] = value
            match = _build_match_series(df, col, str(value), user_query=user_query)
            scores += match.astype(int)

    df["_score"] = scores
    candidates = df[df["_score"] > 0].to_dict(orient="records")

    # No metadata match for requested filters.
    if not candidates:
        return []

    return rank_candidates(candidates, mapped_filters, top_k=top_k)
