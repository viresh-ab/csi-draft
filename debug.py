# Save as debug.py and run: python debug.py
import os
os.environ["OPENAI_API_KEY"] = "sk-your-key"  # paste your key

from app.core.intent import classify_intent
from app.retrieval.metadata_search import search_metadata

query = "Show me Healthcare case studies from Canada"  # paste your actual query here

intent_data = classify_intent(query)
print("INTENT:", intent_data)

matches = search_metadata(intent_data.get("filters", {}))
print("\nTOP MATCHES:")
for m in matches:
    print(f"  - {m.get('study_type')} | {m.get('industry')} | {m.get('geography')} | score={m.get('_rank_score')}")