# Architecture Overview — AI Resume Assistant

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                            │
│  http://localhost:8501                                              │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (Streamlit)                   │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────┐   │
│  │  inject_css()    │  │  render_        │  │  render_styled_    │   │
│  │  Custom CSS      │  │  score_gauge()  │  │  list()            │   │
│  │  styling         │  │  Plotly gauge   │  │  HTML feedback     │   │
│  └─────────────────┘  └─────────────────┘  │  cards              │   │
│                           ┌────────────────┐└───────────────────┘   │
│                           │  render_radar()│                        │
│                           │  Plotly radar  │                        │
│                           └────────────────┘                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ATS Gap Analysis (app.py)                                   │  │
│  │  - Keyword coverage metric cards                             │  │
│  │  - Critical/other missing keyword tags                       │  │
│  │  - Matched keyword display                                   │  │
│  │  - Actionable tips (deterministic, no AI)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER (app.py)                        │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Input Handling                                              │    │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌──────────────┐ │    │
│  │  │  file_uploader   │  │  text_area     │  │  mode_radio  │ │    │
│  │  │  (PDF)           │  │  (paste text)  │  │  (RA / ATS)  │ │    │
│  │  └────────┬────────┘  └───────┬────────┘  └──────┬───────┘ │    │
│  │           │                   │                   │          │    │
│  │           ▼                   ▼                   ▼          │    │
│  │  ┌─────────────────────────────────────────────────────┐     │    │
│  │  │  extract_text()  —  PyPDF (for PDFs)                │     │    │
│  │  └─────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Prompt Building                                             │    │
│  │  ┌────────────────────────────┐                              │    │
│  │  │  build_prompt()            │                              │    │
│  │  │  - Rules (JSON only)       │                              │    │
│  │  │  - Schema definition       │                              │    │
│  │  │  - Response quality rules  │                              │    │
│  │  │  - Knowledge (RAG chunks)  │                              │    │
│  │  │  - Resume text             │                              │    │
│  │  │  - Job description (ATS)   │                              │    │
│  │  └──────────────┬─────────────┘                              │    │
│  └─────────────────┼────────────────────────────────────────────┘    │
│                    │                                                 │
│                    ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  API Layer                                                  │    │
│  │  ┌──────────────────────────────────────────────────────┐   │    │
│  │  │  OpenRouter API (via OpenAI SDK)                    │   │    │
│  │  │  model="openrouter/free"                            │   │    │
│  │  │  Endpoint: /v1/chat/completions                     │   │    │
│  │  └──────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Response Processing                                        │    │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐│    │
│  │  │  raw_output      │  │  safe_parse_   │  │ normalize_   ││    │
│  │  │  null guard      │──▶│  json()        │──▶│  score()     ││    │
│  │  └──────────────────┘  │  + regex fallb│  │  avg model+   ││    │
│  │                        │  ack          │  │  breakdown   ││    │
│  │                        └────────────────┘  └──────────────┘│    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Scoring (scoring.py)                                        │    │
│  │  - Deterministic weighted rubric (100% — no AI involved)    │    │
│  │  - 5 categories: Formatting, ATS, Experience, Achievements, │    │
│  │    Skills Relevance                                          │    │
│  │  - LLM provides feedback only (no score)                    │    │
│  │  - ATS gap analysis (keyword matching)                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Output                                                     │    │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐ │    │
│  │  │  generate_pdf_   │  │  download_     │  │  st.metric   │ │    │
│  │  │  report()        │──▶│  button()      │  │  score cards │ │    │
│  │  │  ReportLab       │  │  PDF download  │  └──────────────┘ │    │
│  │  └──────────────────┘  └────────────────┘                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (rag_engine.py)                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Indexing Pipeline                                          │    │
│  │                                                             │    │
│  │  knowledge/*.txt                                            │    │
│  │       │                                                     │    │
│  │       ▼                                                     │    │
│  │  ┌─────────────────────────────────┐                        │    │
│  │  │  _chunk_text() — HEADING-AWARE  │                        │    │
│  │  │  - Splits at ## heading boundaries                      │    │
│  │  │  - Keeps logical sections intact                        │    │
│  │  │  - Falls back to paragraph boundaries                   │    │
│  │  └──────────────┬──────────────────┘                        │    │
│  │                 ▼                                           │    │
│  │  ┌─────────────────────────────────┐                        │    │
│  │  │  SentenceTransformer.encode()   │                        │    │
│  │  │  - bge-small-en-v1.5           │                        │    │
│  │  │  - 384-dim vectors             │                        │    │
│  │  │  - CPU (no GPU needed)          │                        │    │
│  │  └──────────────┬──────────────────┘                        │    │
│  │                 ▼                                           │    │
│  │  ┌─────────────────────────────────┐                        │    │
│  │  │  ChromaDB.add()                 │                        │    │
│  │  │  - Persistent storage          │                        │    │
│  │  │  - Content-hash change detect  │                        │    │
│  │  │  - Includes "domain" metadata  │                        │    │
│  │  └─────────────────────────────────┘                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Retrieval Pipeline (per query)                              │    │
│  │                                                             │    │
│  │  Resume text                                                 │    │
│  │       │                                                     │    │
│  │       ▼                                                     │    │
│  │  ┌─────────────────────────────────┐                        │    │
│  │  │  classify_domain()             │                        │    │
│  │  │  - Embedding similarity        │                        │    │
│  │  │  - 16 domain descriptions     │                        │    │
│  │  │  - Margin-based confidence    │                        │    │
│  │  └──────────────┬──────────────────┘                        │    │
│  │                 │                                            │    │
│  │        ┌────────┴────────┐                                   │    │
│  │        ▼                 ▼                                    │    │
│  │  High margin       Tight margin (< 0.03)                     │    │
│  │  Search 1 domain    Search top 2 domains                     │    │
│  │        │                 │                                    │    │
│  │        └────────┬────────┘                                   │    │
│  │                 ▼                                            │    │
│  │  ┌─────────────────────────────────┐                        │    │
│  │  │  ChromaDB.query(where_filter)  │                        │    │
│  │  │  - Domain-filtered search     │                        │    │
│  │  │  - Fallback to full search    │                        │    │
│  │  └──────────────┬──────────────────┘                        │    │
│  │                 │                                            │    │
│  │                 ▼                                            │    │
│  │             top 3 chunks                                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Dependencies

```
app.py
  ├── rag_engine.py
  │     ├── sentence-transformers (embeddings + domain classification)
  │     └── chromadb (vector storage)
  ├── scoring.py
  │     └── rubric scoring + ATS gap analysis
  ├── streamlit (UI)
  ├── plotly (charts)
  ├── reportlab (PDF)
  ├── pypdf (PDF extraction)
  ├── openai (OpenRouter API)
  └── python-dotenv (env vars)

rag_engine.py
  ├── hashlib (file change detection)
  ├── re (chunking)
  └── pathlib (file discovery)

scoring.py
  └── re (regex patterns for metrics, keyword extraction)
```

## Layered Scoring Model

The scoring pipeline has **three non-overlapping layers** that feed into a single canonical output:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SEMANTIC EXPLANATION LAYER                        │
│  (scoring.py: compute_semantic_matches)                             │
│  - Phrase-level BGE tri-gram embeddings                             │
│  - HARD_MATCH (≥0.80) / SOFT_MATCH (≥0.70)                         │
│  - Returns equivalence examples for UI only; NOT score input        │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CANONICAL JOB FIT SCORE (output)                  │
│  (scoring.py: compute_job_fit_score)                                │
│                                                                      │
│  Job Fit = w₁ × Concept Coverage (+ w₂ × Semantic (+ w₃ × Evidence) │
│                                                                      │
│  Where weights are role-adaptive:                                    │
│   IT_SUPPORT:   concept 60%  semantic 15%  evidence 25%            │
│   SWE:          concept 40%  semantic 35%  evidence 25%            │
│   GENERAL:      concept 45%  semantic 30%  evidence 25%            │
└─────────────────────────────────────────────────────────────────────┘

Layer 1 — Concept Coverage (primary, ~50% avg)
  (scoring.py: extract_concepts + SKILL_CONCEPTS ontology)
  Maps surface phrases → canonical concepts before matching.
  Examples: "network infrastructure" → networking, "Windows Server admin" → windows_server
  Eliminates "absence = 0 meaning" flaw of pure keyword matching.

Layer 2 — Semantic Alignment (meaning, ~25% avg)
  (scoring.py: compute_semantic_matches + BGE embeddings)
  Per-skill grounding: phrase-level cosine similarity between JD and resume.
  Avoids global document similarity failure mode ("good writing ≠ good fit").

Layer 3 — Evidence Strength (confidence bonus, ~25% avg)
  (scoring.py: analyze_ats_gap keyword_coverage)
  Exact token overlap as bonus-only signal; does not heavily penalize absence
  because concept layer already captures meaning.

Supporting layer — Structural Rubric (isolated from JD)
  (scoring.py: score_resume)
  Resume quality: Formatting, ATS Readiness, Experience, Achievements, Skills.
  This is the "Resume Quality" scorecard, NOT job-fit.
  Kept separate so structural quality doesn't contaminate job relevance.
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Streamlit instead of Flask/Django** | No HTML/CSS/JS needed; built-in widgets for file upload, text areas, metrics |
| **ChromaDB instead of Pinecone/Weaviate** | 100% free, no server, file-based persistence |
| **BAAI/bge-small-en-v1.5 instead of OpenAI embeddings** | Zero API cost, runs locally, no data leaves machine |
| **OpenRouter instead of direct OpenAI** | Free tier available, multiple model options, no credit card needed |
| **RAG instead of static knowledge injection** | Token-efficient, scalable to 500+ files, contextually relevant |
| **Embedding-based domain classification** | Uses already-loaded model (zero cost), more accurate than keyword counting |
| **Margin-based domain confidence** | Prevents false high-confidence when #1 and #2 domains are nearly tied |
| **Heading-aware chunking** | Keeps logical sections intact (## headings), eliminates mid-sentence fragments |
| **Concept ontology (SKILL_CONCEPTS)** | Canonical concept map (~40 concepts, ~200 phrase variants) normalizes language variation before matching. Primary matching layer. |
| **Role-adaptive scoring weights** | IT_SUPPORT / SOFTWARE_ENGINEER / GENERAL presets prevent systemic bias across job types |
| **Semantic as explanation, not score input** | Phrase-level BGE matches shown as "AI-equivalences" in UI; does not inflate scores |
| **Evidence as bonus-only** | Exact keyword overlap boosts confidence; absence doesn't heavily penalize (concepts capture meaning) |
| **Single canonical Job Fit Score** | One authoritative JD-specific number (0-100) from fused concept + semantic + evidence layers. Eliminates multi-metric confusion. |
| **Separate Resume Quality score** | Deterministic rubric (formatting, experience, achievements) shown alongside — distinct from job relevance |
| **ATS gap analysis with concept layer** | Shows both keyword-level and concept-level coverage; semantically bridged gaps highlighted |
| **Knowledge files as recruiter guidance** | Not keyword lists — actual evaluation criteria the LLM wouldn't know |
