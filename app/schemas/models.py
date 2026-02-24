from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    query: str

    class Config:
        json_schema_extra = {
            "examples": [
                {"query": "Show me fintech case studies from India"},
                {"query": "Write a LinkedIn post about our BFSI work in Mumbai"},
                {"query": "Draft a cold email using our retail case study from 2023"},
            ]
        }


class CaseStudyMatch(BaseModel):
    file_path: str
    industry: str
    metadata: dict
    relevance_score: float


class QueryResponse(BaseModel):
    intent: str                              # "retrieve" or "generate"
    content_format: Optional[str] = None    # e.g. "LinkedIn post", null if retrieve
    matched_case_studies: list[CaseStudyMatch]
    generated_content: Optional[str] = None  # Populated only if intent = "generate"
