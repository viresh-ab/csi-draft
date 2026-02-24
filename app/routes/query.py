from fastapi import APIRouter, HTTPException
from app.schemas.models import QueryRequest, QueryResponse, CaseStudyMatch
from app.core.intent import classify_intent
from app.retrieval.metadata_search import search_metadata
from app.retrieval.document_loader import load_from_file_path
from app.generation.content_generator import generate_content

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    Unified query endpoint.
    - Retrieve intent  → returns matched case studies + metadata
    - Generate intent  → retrieves best match, then generates requested content
    """
    query = request.query

    # Step 1: Classify intent + extract filters
    intent_data = classify_intent(query)
    intent = intent_data.get("intent", "retrieve")
    content_format = intent_data.get("content_format")
    filters = intent_data.get("filters", {})

    # Step 2: Search + rank metadata CSV
    matches = search_metadata(filters)
    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No matching case studies found. Try broadening your query."
        )

    # Step 3: Load document using file_path column from CSV
    top_match = matches[0]
    csv_file_path = top_match.get("file_path", "")

    if not csv_file_path or str(csv_file_path) == "nan":
        raise HTTPException(
            status_code=500,
            detail=f"Matched case study has no file_path in metadata: {top_match.get('file_name')}"
        )

    try:
        doc = load_from_file_path(str(csv_file_path))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Step 4: Generate content if requested
    generated = None
    if intent == "generate" and content_format:
        generated = generate_content(
            case_study_text=doc["content"],
            content_format=content_format,
            user_query=query
        )

    return QueryResponse(
        intent=intent,
        content_format=content_format,
        matched_case_studies=[
            CaseStudyMatch(
                file_path=doc["file_path"],
                industry=str(top_match.get("industry", "")),
                metadata=top_match,
                relevance_score=float(top_match.get("_rank_score", 0.0))
            )
        ],
        generated_content=generated
    )
