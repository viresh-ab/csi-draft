# CSI Engine — Case Study Intelligence Engine

Retrieve case studies and generate sales-ready content using AI.

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key in .env
cp .env.example .env
# Edit .env → add OPENAI_API_KEY=sk-...

# Run Streamlit (recommended)
streamlit run streamlit_app.py

# OR run FastAPI
uvicorn app.main:app --reload
```

---

## Hosting on Streamlit Cloud

1. Push this repo to GitHub (make sure `data/` is included or use Git LFS)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New App
3. Select your repo, branch `main`, main file `streamlit_app.py`
4. Click **Advanced settings** → **Secrets** → add:
   ```
   OPENAI_API_KEY = "sk-your-key-here"
   ```
5. Deploy

---

## Project Structure

```
csi-engine/
├── streamlit_app.py       ← Main UI (run this)
├── app/
│   ├── core/              ← Config + intent classification
│   ├── retrieval/         ← Metadata search, document loading, ranking
│   ├── generation/        ← LLM content generation
│   ├── routes/            ← FastAPI routes (optional, for API use)
│   └── schemas/           ← Pydantic models
├── data/
│   ├── metadata.csv       ← Case study index
│   └── cs-files/          ← PDF case studies organised by industry
├── .streamlit/
│   ├── secrets.toml       ← API key (local only, never commit)
│   └── config.toml        ← Theme config
└── requirements.txt
```

---

## Example Queries

| Intent | Example |
|--------|---------|
| Retrieve | `Show me Healthcare case studies from Canada` |
| Generate | `Write a LinkedIn post about our Electronics research in India` |
| Generate | `Draft a cold email based on our Retail mystery shopping study` |
| Generate | `Create an executive summary of our HNI brand study` |
| Generate | `Write a blog post about our Travel loyalty research in Europe` |

---

## Metadata CSV Columns

`sl_no · file_name · file_path · year · client_category · industry · geography · methodology · sample_size · target_respondent · study_type · study_objective · summary · tags · business_impact`
