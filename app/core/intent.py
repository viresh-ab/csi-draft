from openai import OpenAI
import json
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

INTENT_PROMPT = """
You are an intent classifier for a case study intelligence system.

Given a user query, return a JSON object with exactly these keys:
- "intent": "retrieve" if the user only wants to find/view case studies,
            "generate" if the user wants content created (blog, post, email, summary, etc.)
- "content_format": null if intent is "retrieve", otherwise the format as a short string
  e.g. "blog post", "LinkedIn post", "cold email", "tweet thread", "executive summary",
       "sales pitch", "case study narrative", "newsletter section", etc.
- "filters": a dict of any detectable filters from the query. Possible keys:
    industry, geography, methodology, keywords, year, client_type, sample_size
  Leave a key out if not mentioned. Values should be plain strings.

Return ONLY valid JSON. No explanation, no markdown.

Query: {query}
"""


def classify_intent(query: str) -> dict:
    """
    Classifies the user query into intent + content format + filters.

    Returns a dict like:
    {
        "intent": "generate",
        "content_format": "LinkedIn post",
        "filters": { "industry": "BFSI", "geography": "Mumbai" }
    }
    """
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": INTENT_PROMPT.format(query=query)}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
