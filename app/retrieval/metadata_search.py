import pandas as pd
from app.core.config import METADATA_PATH
from app.retrieval.ranker import rank_candidates

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


def search_metadata(filters: dict, top_k: int = 3) -> list[dict]:
    """
    Retrieves and ranks case study candidates from the CSV.

    Maps intent classifier filter keys to actual CSV column names,
    scores each row, then passes to ranker for weighted re-ranking.
    """
    df = load_metadata()
    filters = filters or {}

    # Avoid returning arbitrary files when we couldn't infer any filters.
    if not filters:
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
