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
        "tags": "lending, retail banking",
        "client_category": "Fortune 500",
        "year": 2023
    },
    {
        "industry": "Healthcare",
        "file_name": "apollo_patient_journey.pdf",
        "geography": "Chennai",
        "methodology": "Ethnography",
        "tags": "patient experience, hospital",
        "client_category": "Enterprise",
        "year": 2022
    },
    {
        "industry": "Retail",
        "file_name": "dmart_shopper_study.pdf",
        "geography": "Pune",
        "methodology": "Focus Groups",
        "tags": "retail, shopper behavior",
        "client_category": "SMB",
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
    assert results == []


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_no_filters_returns_empty(mock_load):
    results = search_metadata({})
    assert results == []


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_browse_all_query_returns_top_k(mock_load):
    results = search_metadata({}, top_k=2, user_query="List all case studies")
    assert len(results) == len(MOCK_CSV_DATA)
    assert all("_rank_score" not in r for r in results)


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_infers_geography_from_query_when_filters_empty(mock_load):
    results = search_metadata({}, user_query="Show me studies in Chennai")
    assert len(results) >= 1
    assert results[0]["geography"] == "Chennai"


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_search_returns_top_k(mock_load):
    results = search_metadata({"year": "2023"}, top_k=2)
    assert len(results) <= 2


@patch("app.retrieval.metadata_search.load_metadata", return_value=MOCK_CSV_DATA)
def test_results_have_rank_score(mock_load):
    results = search_metadata({"industry": "Healthcare"})
    for r in results:
        assert "_rank_score" in r
