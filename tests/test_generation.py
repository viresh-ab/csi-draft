"""
Tests for content_generator.py

Run with: pytest tests/test_generation.py -v
"""
import pytest
from unittest.mock import patch, MagicMock
from app.generation.content_generator import generate_content


MOCK_CASE_STUDY = """
Client: HDFC Bank
Industry: BFSI
Objective: Understand loan rejection experiences among first-time borrowers.
Methodology: 200 in-depth interviews across Mumbai and Pune.
Key Findings: 72% of rejected applicants had no clear communication on rejection reason.
Outcome: HDFC redesigned their rejection notification workflow, reducing complaints by 35%.
"""


@patch("app.generation.content_generator.client")
def test_generate_linkedin_post(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Here is your LinkedIn post..."
    mock_client.chat.completions.create.return_value = mock_response

    result = generate_content(
        case_study_text=MOCK_CASE_STUDY,
        content_format="LinkedIn post",
        user_query="Write a LinkedIn post about our BFSI work"
    )

    assert isinstance(result, str)
    assert len(result) > 0
    mock_client.chat.completions.create.assert_called_once()


@patch("app.generation.content_generator.client")
def test_generate_blog_post(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Here is your blog post..."
    mock_client.chat.completions.create.return_value = mock_response

    result = generate_content(
        case_study_text=MOCK_CASE_STUDY,
        content_format="blog post",
        user_query="Create a blog post about HDFC loan research"
    )

    assert isinstance(result, str)


@patch("app.generation.content_generator.client")
def test_long_case_study_is_truncated(mock_client):
    """Ensures text longer than 12000 chars is truncated before API call."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Generated."
    mock_client.chat.completions.create.return_value = mock_response

    long_text = "A" * 20000

    generate_content(
        case_study_text=long_text,
        content_format="executive summary",
        user_query="Summarize this"
    )

    call_args = mock_client.chat.completions.create.call_args
    prompt_used = call_args.kwargs["messages"][0]["content"]
    # The case study portion should be capped at 12000 chars
    assert long_text not in prompt_used
