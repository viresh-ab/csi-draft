from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

GENERATION_PROMPT = """
You are a senior content strategist for a research and insights firm.

You have been provided the full text of a case study. Your task is to produce a {content_format} based on this case study.

Guidelines:
- Follow the conventions, structure, and tone typical of a professional {content_format}.
- Be specific — use real details, numbers, methodologies, and outcomes from the case study.
- Do NOT fabricate any data, names, or statistics not present in the case study.
- Tailor the output to the user's exact request (see below).
- Keep it compelling, clear, and ready to use with minimal editing.

--- CASE STUDY ---
{case_study_text}
--- END OF CASE STUDY ---

User's exact request: "{user_query}"

Now generate the {content_format}:
"""


def generate_content(
    case_study_text: str,
    content_format: str,
    user_query: str
) -> str:
    """
    Generates content of any format from a case study.

    Args:
        case_study_text : Full extracted text of the case study document
        content_format  : Desired output format (e.g. "blog post", "LinkedIn post")
        user_query      : Original user query for additional context/nuance

    Returns:
        Generated content as a string.
    """
    prompt = GENERATION_PROMPT.format(
        content_format=content_format,
        case_study_text=case_study_text[:12000],  # Stay within context window
        user_query=user_query
    )

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
