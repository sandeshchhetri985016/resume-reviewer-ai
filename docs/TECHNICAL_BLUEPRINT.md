# Technical Blueprint — AI Resume Assistant

## 1. Tech Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **UI Framework** | Streamlit | latest | Fastest way to build data-centric web UI in Python; no HTML/CSS/JS required |
| **LLM Gateway** | OpenRouter API | N/A | Free tier with multiple models; OpenAI-compatible SDK; no credit card needed |
| **Embedding Model** | BAAI/bge-small-en-v1.5 | 1.5 (sentence-transformers) | 384-dim, runs locally on CPU, better quality than MiniLM, no API costs |
| **Vector Database** | ChromaDB | latest | Local persistent vector store; no server setup; file-based storage |
| **PDF Extraction** | PyPDF | latest | Extracts text from uploaded PDF resumes |
| **PDF Generation** | ReportLab | latest | Generates downloadable analysis reports |
| **Visualization** | Plotly | latest | Interactive gauge and radar charts |
| **Configuration** | python-dotenv | latest | Loads API keys from .env file |
| **Language** | Python | 3.13 | Project language |
| **OS** | Windows 11 | N/A | Development environment |

## 2. Project Structure

```
resume-reviewer/
├── app.py                       # Main entry point — Streamlit application
├── rag_engine.py                # RAG pipeline: chunking, embeddings, classification, retrieval
├── scoring.py                   # Deterministic rubric scoring + ATS gap analysis
├── requirements.txt             # Python dependencies
├── .env.example                 # API key template (copy to .env)
├── .env                         # OPENROUTER_API_KEY (NOT committed)
├── .gitignore                   # Excludes chroma_db/, .env, archive/, __pycache__/
│
├── docs/                        # Portfolio documentation
│   ├── PRODUCT_REQUIREMENTS.md  # PRD: problem statement, user stories, requirements
│   ├── TECHNICAL_BLUEPRINT.md   # This file — tech stack, data flow, API contract
│   ├── ARCHITECTURE.md          # System architecture diagram and dependencies
│   ├── SPRINT_LOG.md            # Sprint-by-sprint development changelog (12 sprints)
│   ├── USER_STORY.md            # Full Mermaid flowchart of user interaction paths
│   └── RAG_EXPLAINER.md         # Plain-English RAG pipeline explanation
│
├── scripts/                     # Utility scripts (not used in main app)
│   └── rag_demo.py              # Terminal demo for testing RAG without UI
│
├── archive/                     # Legacy code (kept for reference, not used in app)
│   ├── main.py                  # CLI-only resume analysis (legacy entry point)
│   ├── validators.py            # JSON schema validation (legacy)
│   └── scoring_engine.py        # Local keyword scoring (legacy, healthcare-focused)
│
├── knowledge/                   # Career domain knowledge files for RAG
│   ├── ats_tips.txt             # ATS system best practices
│   ├── healthcare_keywords.txt  # Healthcare resume evaluation guidance
│   ├── resume_best_practices.txt # General resume writing best practices
│   └── ... (15 more domain files)  # Actionable recruiter guidance per domain
│
└── chroma_db/                   # Local vector database (auto-created, git-ignored)
    └── ...                      # ChromaDB persistent storage files
```

## 3. Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│  User Input   │───▶│  app.py      │───▶│  build_prompt()  │
│  PDF / Text   │    │  (Streamlit) │    └────────┬─────────┘
└──────────────┘    └──────┬───────┘             │
                           │                     │
                           │              ┌──────┴──────┐
                           │              │  rag_engine  │
                           │              │  .retrieve() │
                           │              │  (domain-    │
                           │              │   filtered)  │
                           │              └──────┬──────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────────────────────────┐
                    │      Model Retry Loop              │
                    │  Try openrouter/free               │
                    │  If fails → try fallback models    │
                    │  Validate JSON before accepting    │
                    └──────────────┬───────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │      Response Processing          │
                    │  safe_parse_json()                │
                    │  score_resume() (rubric only)     │
                    └──────────────┬───────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │         Output Rendering          │
                    │  Score cards (100% rubric)        │
                    │  Score gauge + radar chart        │
                    │  Rubric breakdown (expanded)      │
                    │  Styled feedback cards            │
                    │  ATS keyword gap analysis         │
                    │  PDF download                     │
                    └──────────────────────────────────┘
```

## 4. RAG Pipeline Architecture

### Indexing (runs on first startup, or when files change)

```
knowledge/*.txt
      │
      ▼
  _chunk_text() — HEADING-AWARE
  - Detects ## boundaries to keep logical sections
  - Falls back to paragraph breaks, then sentence splits
  - Each chunk is a self-contained semantic unit
      │
      ▼
  SentenceTransformer.encode()
  - BAAI/bge-small-en-v1.5
  - 384-dimensional vectors
  - Runs on CPU
      │
      ▼
  ChromaDB.add()
  - Persistent storage in chroma_db/
  - Stores: vector, text, source_file, chunk_index, domain
  - Content-hash change detection
```

### Retrieval (per query)

```
User resume text
      │
      ▼
  classify_domain() — EMBEDDING-BASED
  - Cosine similarity against 16 domain descriptions
  - Returns best domain + similarity score
  - Zero extra cost (model already loaded for RAG)
      │
      ▼
  Margin check
  ├── margin vs #2 < 0.03 → search top 2 domains (tie)
  ├── sim ≥ 0.6 → search 1 domain (high confidence)
  ├── sim ≥ 0.4 → search top 2 domains
  └── sim < 0.4 → search all domains
      │
      ▼
  ChromaDB.query(where={"domain": {"$in": [...]}})
  - Domain-filtered vector search
  - Fallback to full search if no results
      │
      ▼
  Top 3 chunks injected into LLM prompt
  (relevant to detected domain only)
```

## 5. Database Schema (ChromaDB)

ChromaDB is schemaless. Each stored record contains:

| Field | Type | Example |
|-------|------|---------|
| `id` | str | `software_engineering_chunk_3` |
| `embedding` | List[float] | 384 floats |
| `document` | str | Full chunk text (heading-aware) |
| `metadata.source_file` | str | `software_engineering.txt:md5hash` |
| `metadata.chunk_index` | int | 3 |
| `metadata.text` | str | Full chunk text (duplicate) |
| `metadata.domain` | str | `software_engineering` |

## 6. Scoring Rubric

The `scoring.py` module produces a deterministic score using 5 weighted categories:

| Category | Weight | What It Measures |
|----------|--------|-----------------|
| Formatting | 15% | Sections present, bullet points, contact info |
| ATS Readiness | 20% | Keyword density, required sections, job titles |
| Experience Quality | 25% | Years of experience, number of roles, progression |
| Achievement Density | 20% | Quantified claims vs total bullets, action verbs |
| Skills Relevance | 20% | Skills section, education, soft/hard balance |

Final score = **rubric_score** (100%). No AI involvement. Score is reproducible — same resume always gets the same score.

The LLM provides qualitative feedback only: summary, strengths, weaknesses, improvements.

## 7. ATS Keyword Gap Analysis

In ATS Job Match mode, `analyze_ats_gap()` runs deterministically:

- Extracts unigrams + bigrams from resume and job description
- Removes stop words, finds matched vs missing keywords
- Categorizes missing as **critical** (appears 2+ times in JD) or **other**
- Returns: `coverage%`, `matched_count`, `missing_count`, keyword lists

Rendered as 3 metric cards + color-coded tag clouds (red=critical, amber=other, green=matched).

## 8. API Contract (OpenRouter)

**Endpoint:** `POST https://openrouter.ai/api/v1/chat/completions`

**Model Strategy:**
```python
FREE_MODELS = [
    "openrouter/free",                    # Try first (auto-routing)
    "nvidia/nemotron-nano-12b-v2-vl:free", # Fallback
    "meta/llama-3.2-3b-instruct:free",     # Fallback
]
```

Each response is validated as JSON before accepting. If all models fail, user sees a clear error message.

**Request:**
```json
{
  "model": "openrouter/free",
  "messages": [
    {
      "role": "user",
      "content": "[prompt with rules + knowledge + resume — no score schema]"
    }
  ]
}
```

**Response (parsed):**
```json
{
  "summary": "Concise professional summary (max 50 words)",
  "strengths": [
    "Complete sentence referencing specific resume content",
    "At least 8 words, specific to the candidate's experience"
  ],
  "weaknesses": [
    "Complete sentence identifying a real gap",
    "Specific to what's missing from this resume"
  ],
  "improvements": [
    "Actionable suggestion with concrete example",
    "Tied to the candidate's actual experience"
  ]
}
```

Note: No `score` or `breakdown` in the LLM response. Scoring is 100% deterministic from the rubric.

## 9. Configuration

| Variable | Location | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `.env` | None | API key for OpenRouter |
| `EMBEDDING_MODEL_NAME` | `rag_engine.py` | `BAAI/bge-small-en-v1.5` | sentence-transformers model |
| `CHUNK_MIN_CHARS` | `rag_engine.py` | 300 | Minimum chunk size |
| `CHUNK_MAX_CHARS` | `rag_engine.py` | 500 | Maximum chunk size |
| `CHUNK_OVERLAP` | `rag_engine.py` | 50 | Chunk overlap |
| `RETRIEVE_TOP_K` | `rag_engine.py` | 3 | Chunks per query |
| `FREE_MODELS` | `app.py` | 3 models | Model retry fallback list |
| 16 `DOMAIN_DESCRIPTIONS` | `rag_engine.py` | N/A | Embedding-based domain classifier |

## 10. Dependencies

```
openai                 # OpenRouter API client
python-dotenv          # .env loading
streamlit              # Web UI framework
pypdf                  # PDF text extraction
plotly                 # Charts (gauge + radar)
reportlab              # PDF report generation
sentence-transformers  # Local text embeddings (RAG + domain classification)
chromadb               # Local vector database (RAG)
torchvision            # Required by transformers dependency