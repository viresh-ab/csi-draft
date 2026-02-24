import pandas as pd
from app.core.config import METADATA_PATH
from app.retrieval.ranker import rank_candidates


BROWSE_ALL_PHRASES = (
    "all case studies",
    "list case studies",
    "list all",
    "show all",
    "all studies",
)

# Maps intent classifier filter keys → actual CSV column names
FILTER_COLUMN_MAP = {
    "industry":    "industry",
    "geography":   "geography",
    "methodology": "methodology",
    "keywords":    "tags",          # intent says 'keywords', CSV has 'tags'
    "tags":        "tags",
    "year":        "year",
    "client_type": "client_category",  # intent says 'client_type', CSV has 'client_category'
    "client_category": "client_category",
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
            return df.head(top_k).to_dict(orient="records")
        return []

    scores = pd.Series([0] * len(df), dtype=int)

    # Remap filter keys to actual CSV columns before searching
    mapped_filters = {}
    for key, value in filters.items():
        col = FILTER_COLUMN_MAP.get(key, key)
        if value and col in df.columns:
            mapped_filters[col] = value
            match = df[col].astype(str).str.lower().str.contains(
                str(value).lower(), na=False
            )
            scores += match.astype(int)

    df["_score"] = scores
    candidates = df[df["_score"] > 0].to_dict(orient="records")

    # No metadata match for requested filters.
    if not candidates:
        return []

    return rank_candidates(candidates, mapped_filters, top_k=top_k)
