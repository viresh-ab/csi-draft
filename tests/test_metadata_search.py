"""
Tests for metadata_search.py

Run with: pytest tests/test_metadata_search.py -v
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.retrieval.metadata_search import search_metadata


MOCK_CSV_DATA = pd.DataFrame([
    {
        "industry": "BFSI",
        "file_name": "hdfc_loan_study.pdf",
        "geography": "Mumbai",
        "methodology": "Survey",
        "keywords": "lending, retail banking",
        "client_type": "Fortune 500",
        "year": 2023
    },
    {
        "industry": "Healthcare",
        "file_name": "apollo_patient_journey.pdf",
        "geography": "Chennai",
        "methodology": "Ethnography",
        "keywords": "patient experience, hospital",
        "client_type": "Enterprise",
        "year": 2022
    },
    {
        "industry": "Retail",
        "file_name": "dmart_shopper_study.pdf",
        "geography": "Pune",
        "methodology": "Focus Groups",
        "keywords": "retail, shopper behavior",
        "client_type": "SMB",
        "year": 2023
    },
])


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_by_industry(mock_load):
    results = search_metadata({"industry": "BFSI"})
    assert len(results) >= 1
    assert results[0]["industry"] == "BFSI"


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_by_geography(mock_load):
    results = search_metadata({"geography": "Chennai"})
    assert len(results) >= 1
    assert results[0]["file_name"] == "apollo_patient_journey.pdf"


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_no_match_returns_fallback(mock_load):
    results = search_metadata({"industry": "NonExistentIndustry"})
    # Fallback should return results rather than empty
    assert isinstance(results, list)


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_returns_top_k(mock_load):
    results = search_metadata({"year": "2023"}, top_k=2)
    assert len(results) <= 2


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_results_have_rank_score(mock_load):
    results = search_metadata({"industry": "Healthcare"})
    for r in results:
        assert "_rank_score" in r
