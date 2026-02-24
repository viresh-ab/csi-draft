"""
CSI Engine — Streamlit Frontend
Calls Python functions directly (no HTTP) — works on Streamlit Cloud.
"""
import sys
import os
from pathlib import Path
import streamlit as st

# ── Ensure the app/ package is importable ────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CSI Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.stApp                       { background-color: #0f0f13; color: #e8e6e0; }
section[data-testid="stSidebar"] { background-color: #16161d; border-right: 1px solid #2a2a35; }

.csi-header  { font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800;
               color:#f0ede6; letter-spacing:-0.03em; line-height:1.1; margin-bottom:0.2rem; }
.csi-tagline { font-size:0.78rem; color:#6b6b7a; letter-spacing:0.14em;
               text-transform:uppercase; margin-bottom:2rem; }

.stTextArea textarea {
    background-color:#1a1a24 !important; border:1px solid #2e2e3e !important;
    border-radius:8px !important; color:#e8e6e0 !important;
    font-size:0.95rem !important; padding:14px !important; }
.stTextArea textarea:focus {
    border-color:#c8a97e !important;
    box-shadow:0 0 0 2px rgba(200,169,126,0.15) !important; }

.stButton > button {
    background-color:#c8a97e !important; color:#0f0f13 !important;
    border:none !important; border-radius:6px !important;
    font-family:'Syne',sans-serif !important; font-weight:700 !important;
    font-size:0.88rem !important; letter-spacing:0.05em !important;
    padding:0.6rem 1.8rem !important; text-transform:uppercase; }
.stButton > button:hover {
    background-color:#d9bc94 !important;
    box-shadow:0 4px 16px rgba(200,169,126,0.3) !important; }

.result-card  { background:#1a1a24; border:1px solid #2a2a35;
                border-radius:10px; padding:1.4rem 1.6rem; margin-bottom:1rem; }
.result-title { font-family:'Syne',sans-serif; font-size:1.05rem; font-weight:700;
                color:#f0ede6; margin-bottom:0.6rem; }
.meta-tag     { background:#22222e; padding:2px 10px; border-radius:20px;
                color:#a0a0b0; font-size:0.73rem; display:inline-block; margin:2px 4px 2px 0; }
.score-badge  { background:#c8a97e22; color:#c8a97e; border:1px solid #c8a97e44;
                padding:2px 10px; border-radius:20px; font-size:0.73rem;
                font-weight:600; display:inline-block; }
.intent-retrieve { background:#1e3a2e; color:#4ade80; border:1px solid #2d5c3e;
                   padding:4px 14px; border-radius:20px; font-size:0.78rem;
                   font-weight:600; display:inline-block; margin-bottom:1.2rem; }
.intent-generate { background:#2a1e3a; color:#c084fc; border:1px solid #4a2e6a;
                   padding:4px 14px; border-radius:20px; font-size:0.78rem;
                   font-weight:600; display:inline-block; margin-bottom:1.2rem; }
.generated-box   { background:#13131c; border:1px solid #c8a97e44;
                   border-left:3px solid #c8a97e; border-radius:8px;
                   padding:1.6rem; font-size:0.92rem; line-height:1.8;
                   color:#d8d6d0; white-space:pre-wrap; }
.section-label   { font-family:'Syne',sans-serif; font-size:0.7rem; font-weight:700;
                   letter-spacing:0.14em; text-transform:uppercase; color:#6b6b7a;
                   margin-bottom:0.8rem; margin-top:1.4rem; }
.file-path       { font-family:monospace; font-size:0.72rem; color:#4a4a5a; margin-top:0.5rem; }
.history-item    { background:#1a1a24; border-radius:6px; padding:0.55rem 0.8rem;
                   margin-bottom:0.35rem; font-size:0.78rem; color:#7a7a8a;
                   border:1px solid #22222e; }
.sidebar-label   { font-family:'Syne',sans-serif; font-size:0.68rem; font-weight:700;
                   letter-spacing:0.12em; text-transform:uppercase; color:#4b4b5a;
                   margin-bottom:0.3rem; }
div[data-testid="stExpander"] { background:#1a1a24 !important;
                                 border:1px solid #2a2a35 !important; border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Load API key from Streamlit secrets or environment ────────────────────────
def get_openai_key() -> str:
    # Streamlit Cloud: set in App Settings → Secrets as OPENAI_API_KEY = "sk-..."
    if hasattr(st, "secrets"):
        try:
            if "OPENAI_API_KEY" in st.secrets:
                return st.secrets["OPENAI_API_KEY"]
        except Exception:
            # In local/dev environments secrets.toml may not exist.
            pass
    return os.environ.get("OPENAI_API_KEY", "")

# ── Lazy-import backend modules (after path is set) ───────────────────────────
@st.cache_resource
def load_modules():
    """Import backend modules once and cache them."""
    key = get_openai_key()
    if not key:
        return None, None, None, None
    os.environ["OPENAI_API_KEY"] = key
    from app.core.intent import classify_intent
    from app.retrieval.metadata_search import search_metadata
    from app.retrieval.document_loader import load_from_file_path
    from app.generation.content_generator import generate_content
    return classify_intent, search_metadata, load_from_file_path, generate_content

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "chat_turns" not in st.session_state:
    st.session_state.chat_turns = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='margin-bottom:1.8rem;padding-bottom:1.2rem;border-bottom:1px solid #2a2a35;'>
            <div style='font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;
                        color:#f0ede6;letter-spacing:-0.02em;'>CSI Engine</div>
            <div style='font-size:0.68rem;color:#4b4b5a;letter-spacing:0.12em;
                        text-transform:uppercase;margin-top:3px;'>Case Study Intelligence</div>
        </div>
    """, unsafe_allow_html=True)

    # API Key input (for local use; on Streamlit Cloud use secrets)
    if not get_openai_key():
        st.markdown('<div class="sidebar-label">OpenAI API Key</div>', unsafe_allow_html=True)
        manual_key = st.text_input("key", type="password", placeholder="sk-...", label_visibility="collapsed")
        if manual_key:
            os.environ["OPENAI_API_KEY"] = manual_key
            st.rerun()
    else:
        st.success("✓ API key loaded")

    # Quick stats
    try:
        from app.core.config import METADATA_PATH, CS_ROOT
        import pandas as pd
        if METADATA_PATH.exists():
            df = pd.read_csv(METADATA_PATH)
            st.markdown(f"""
                <div style='background:#1a1a24;border:1px solid #2a2a35;border-radius:8px;
                            padding:0.8rem 1rem;margin-top:0.5rem;font-size:0.78rem;color:#a0a0b0;'>
                    📄 <b style='color:#e8e6e0;'>{len(df)}</b> case studies<br/>
                    🏭 <b style='color:#e8e6e0;'>{df['industry'].nunique() if 'industry' in df.columns else '—'}</b> industries
                </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass

    # Recent queries
    if st.session_state.history:
        st.markdown("---")
        st.markdown('<div class="sidebar-label">Recent Queries</div>', unsafe_allow_html=True)
        for item in reversed(st.session_state.history[-8:]):
            color = "#c084fc" if item["intent"] == "generate" else "#4ade80"
            st.markdown(f"""
                <div class="history-item">
                    <span style='color:{color};font-size:0.65rem;text-transform:uppercase;
                                 font-weight:600;letter-spacing:0.08em;'>{item['intent']}</span><br/>
                    {item['query'][:60]}{'...' if len(item['query']) > 60 else ''}
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div style="font-size:0.68rem;color:#3a3a4a;text-align:center;">CSI Engine v1.0</div>', unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────
main_col, _ = st.columns([3, 1])

with main_col:
    st.markdown('<div class="csi-header">Case Study Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="csi-tagline">Retrieve · Analyse · Generate</div>', unsafe_allow_html=True)

    # Example buttons
    st.markdown("**Try an example:**")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔍  Healthcare studies — Canada", use_container_width=True):
            st.session_state.query_text = "Show me Healthcare case studies from Canada"
            st.rerun()
    with c2:
        if st.button("✍️  LinkedIn post — Electronics", use_container_width=True):
            st.session_state.query_text = "Write a LinkedIn post about our Electronics research in India"
            st.rerun()
    with c3:
        if st.button("📝  Blog post — Retail", use_container_width=True):
            st.session_state.query_text = "Write a blog post based on our retail customer satisfaction study"
            st.rerun()

    st.markdown("")

    # Query input
    query = st.text_area(
        label="Query",
        value=st.session_state.query_text,
        placeholder=(
            "Ask anything — retrieve case studies or generate content from them...\n\n"
            "Examples:\n"
            "• Show me Healthcare case studies from Canada\n"
            "• Write a LinkedIn post about our Electronics research in India\n"
            "• Draft a cold email based on our Retail mystery shopping study\n"
            "• Create an executive summary of our HNI brand study in India\n"
            "• Write a blog post about our Travel loyalty research in Europe"
        ),
        height=160,
        label_visibility="collapsed"
    )

    btn_col, _ = st.columns([1, 5])
    with btn_col:
        run = st.button("Run Query →", use_container_width=True)

    # ── Execute ───────────────────────────────────────────────────────────────
    if run:
        if not get_openai_key() and not os.environ.get("OPENAI_API_KEY"):
            st.error("Please enter your OpenAI API key in the sidebar first.")
        elif not query.strip():
            st.warning("Please enter a query first.")
        else:
            st.session_state.chat_turns.append({"role": "user", "query": query})
            classify_intent, search_metadata, load_from_file_path, generate_content = load_modules()

            if not classify_intent:
                st.error("Could not load backend — check your OpenAI API key.")
            else:
                with st.spinner("Thinking..."):
                    try:
                        # Step 1: Intent + filters
                        intent_data    = classify_intent(query)
                        intent         = intent_data.get("intent", "retrieve")
                        content_format = intent_data.get("content_format")
                        filters        = intent_data.get("filters", {})

                        # Step 2: Retrieve from metadata
                        matches = search_metadata(filters, user_query=query)

                        if not matches:
                            st.session_state.chat_turns.append({
                                "role": "assistant",
                                "intent": intent,
                                "content_format": content_format,
                                "warning": "No matching case studies found. Try broader terms.",
                                "matches": [],
                                "generated": None,
                            })
                        else:
                            top_match      = matches[0]
                            csv_file_path  = str(top_match.get("file_path", ""))

                            # Step 3: Load document
                            doc = load_from_file_path(csv_file_path)

                            # Step 4: Generate if needed
                            generated = None
                            if intent == "generate" and content_format:
                                generated = generate_content(
                                    case_study_text=doc["content"],
                                    content_format=content_format,
                                    user_query=query
                                )

                            # Save history
                            st.session_state.history.append({"query": query, "intent": intent})
                            st.session_state.chat_turns.append({
                                "role": "assistant",
                                "intent": intent,
                                "content_format": content_format,
                                "warning": None,
                                "matches": matches,
                                "generated": generated,
                            })

                    except FileNotFoundError as e:
                        st.error(f"File not found: {e}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.exception(e)

    # Chat-style transcript
    st.markdown("---")
    st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)

    for idx, turn in enumerate(st.session_state.chat_turns):
        if turn.get("role") == "user":
            with st.chat_message("user"):
                st.markdown(turn.get("query", ""))
            continue

        with st.chat_message("assistant"):
            intent = turn.get("intent", "retrieve")
            content_format = turn.get("content_format")
            matches = turn.get("matches", [])
            generated = turn.get("generated")
            warning = turn.get("warning")

            if intent == "generate":
                st.markdown(
                    f'<div class="intent-generate">✦ Generate &nbsp;·&nbsp; {content_format or "Content"}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="intent-retrieve">✦ Retrieve</div>', unsafe_allow_html=True)

            if warning:
                st.warning(warning)
                continue

            st.markdown('<div class="section-label">Matched Case Studies</div>', unsafe_allow_html=True)

            for m_idx, match in enumerate(matches):
                meta = match
                file_name = str(meta.get("file_name", "Untitled Study"))
                industry = meta.get("industry", "—")
                geography = meta.get("geography", "")
                methodology = meta.get("methodology", "")
                sample_size = meta.get("sample_size", "")
                year = meta.get("year", "")
                score = float(meta.get("_rank_score", 0))
                summary = meta.get("summary", "")
                file_path = str(meta.get("file_path", ""))

                geo_tag = f'<span class="meta-tag">📍 {geography}</span>' if geography and str(geography) != "nan" else ""
                meth_tag = f'<span class="meta-tag">🔬 {methodology}</span>' if methodology and str(methodology) != "nan" else ""
                size_tag = f'<span class="meta-tag">👥 n={sample_size}</span>' if sample_size and str(sample_size) not in ["", "nan"] else ""
                year_tag = f'<span class="meta-tag">📅 {int(float(year))}</span>' if year and str(year) != "nan" else ""

                st.markdown(f"""
                    <div class="result-card">
                        <div class="result-title">{file_name}</div>
                        <div>
                            <span class="meta-tag">🏭 {industry}</span>
                            {geo_tag}{meth_tag}{size_tag}{year_tag}
                            <span class="score-badge">score {score:.2f}</span>
                        </div>
                        <div class="file-path">{file_path}</div>
                    </div>
                """, unsafe_allow_html=True)

                if file_path and file_path != "nan":
                    candidate_path = Path(file_path)
                    if not candidate_path.is_absolute():
                        candidate_path = Path.cwd() / candidate_path
                    if candidate_path.exists():
                        with open(candidate_path, "rb") as fh:
                            st.download_button(
                                label=f"⬇ Download file: {file_name}",
                                data=fh.read(),
                                file_name=file_name,
                                mime="application/octet-stream",
                                key=f"download_{idx}_{m_idx}",
                            )

                if summary and str(summary) not in ["", "nan"]:
                    with st.expander("View summary"):
                        st.markdown(
                            f"<div style='font-size:0.88rem;color:#a0a0b0;line-height:1.7;'>{summary}</div>",
                            unsafe_allow_html=True,
                        )

            if generated:
                st.markdown('<div class="section-label">Generated Content</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="generated-box">{generated}</div>', unsafe_allow_html=True)
                st.download_button(
                    label="⬇ Download generated text",
                    data=generated,
                    file_name=f"{(content_format or 'output').replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"generated_{idx}",
                )
