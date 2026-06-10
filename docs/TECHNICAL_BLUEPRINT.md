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
├── rag_engine.py                # RAG pipeline: chunking, embeddings, retrieval
├── requirements.txt             # Python dependencies
├── .env.example                 # API key template (copy to .env)
├── .env                         # OPENROUTER_API_KEY (NOT committed)
├── .gitignore                   # Excludes chroma_db/, .env, archive/, __pycache__/
│
├── docs/                        # Portfolio documentation
│   ├── PRODUCT_REQUIREMENTS.md  # PRD: problem statement, user stories, requirements
│   ├── TECHNICAL_BLUEPRINT.md   # This file — tech stack, data flow, API contract
│   ├── ARCHITECTURE.md          # System architecture diagram and dependencies
│   ├── SPRINT_LOG.md            # Sprint-by-sprint development changelog
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
│   ├── healthcare_keywords.txt  # Healthcare keyword lists
│   ├── resume_best_practices.txt # General resume writing best practices
│   └── ... (15 more domain files)  # Accounting, aviation, data science, etc.
│
└── chroma_db/                   # Local vector database (auto-created, git-ignored)
    └── ...                      # ChromaDB persistent storage files
```

## 3. Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│  User Input   │───▶│  app.py      │───▶│  build_prompt()  │
│  PDF / Text   │    │  (Streamlit) │    └────────┬─────────┘
└──────────────┘    └──────────────┘             │
                                                  ▼
                                        ┌──────────────────┐
                                        │  OpenRouter API   │
                                        │  (LLM)            │
                                        └────────┬─────────┘
                                                  │
                                                  ▼
                                        ┌──────────────────┐
                                        │  safe_parse_json()│
                                        │  normalize_score()│
                                        └────────┬─────────┘
                                                  │
                                                  ▼
                              ┌───────────────────────────────┐
                              │  render_score_gauge()         │
                              │  render_radar()               │
                              │  render_styled_list()          │
                              │  generate_pdf_report()         │
                              └───────────────────────────────┘
                                        ▲
                                        │
┌──────────────┐               ┌────────┴─────────┐
│  knowledge/  │──────────────▶│  rag_engine.py    │
│  18 files    │               │  ChromaDB +       │
│  261 chunks  │               │  sentence-transform│
└──────────────┘               └──────────────────┘
```

## 4. RAG Pipeline Architecture

### Indexing (runs on first startup, or when files change)

```
knowledge/*.txt
      │
      ▼
  _chunk_text()
  - Splits into 300-500 char chunks
  - 50 char overlap between chunks
  - Tries sentence/paragraph boundaries
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
  - Stores: vector, text, source_file, chunk_index
  - Content-hash change detection
```

### Retrieval (per query)

```
User resume text
      │
      ▼
  SentenceTransformer.encode([query])
      │
      ▼
  ChromaDB.query(n_results=3)
  - Cosine similarity
  - Returns top 3 chunks + distances
      │
      ▼
  Only 3 chunks injected into LLM prompt
  (vs. ALL files before RAG)
```

## 5. Database Schema (ChromaDB)

ChromaDB is schemaless. Each stored record contains:

| Field | Type | Example |
|-------|------|---------|
| `id` | str | `plumber.txt_chunk_0` |
| `embedding` | List[float] | 384 floats |
| `document` | str | Full chunk text |
| `metadata.source_file` | str | `plumber.txt:md5hash` |
| `metadata.chunk_index` | int | 0 |
| `metadata.text` | str | Full chunk text (duplicate) |

## 6. API Contract (OpenRouter)

**Endpoint:** `POST https://openrouter.ai/api/v1/chat/completions`

**Request:**
```json
{
  "model": "openrouter/free",
  "messages": [
    {
      "role": "user",
      "content": "[full prompt with rules + schema + knowledge + resume]"
    }
  ]
}
```

**Response (parsed):**
```json
{
  "score": 65,
  "summary": "String (max 50 words)",
  "breakdown": {
    "skills": 8,
    "experience": 7,
    "clarity": 6,
    "impact": 5,
    "ats_match": 8
  },
  "strengths": ["Complete sentence 1", "Complete sentence 2"],
  "weaknesses": ["Complete sentence 1", "Complete sentence 2"],
  "improvements": ["Complete sentence 1", "Complete sentence 2"]
}
```

## 7. Configuration

| Variable | Location | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `.env` | None | API key for OpenRouter |
| `EMBEDDING_MODEL_NAME` | `rag_engine.py` | `BAAI/bge-small-en-v1.5` | sentence-transformers model |
| `CHUNK_MIN_CHARS` | `rag_engine.py` | 300 | Minimum chunk size |
| `CHUNK_MAX_CHARS` | `rag_engine.py` | 500 | Maximum chunk size |
| `CHUNK_OVERLAP` | `rag_engine.py` | 50 | Chunk overlap |
| `RETRIEVE_TOP_K` | `rag_engine.py` | 3 | Chunks per query |
| `model` | `app.py` (line 513) | `openrouter/free` | OpenRouter model |

## 8. Dependencies

```
openai                 # OpenRouter API client
python-dotenv          # .env loading
streamlit              # Web UI framework
pypdf                  # PDF text extraction
plotly                 # Charts (gauge + radar)
reportlab              # PDF report generation
sentence-transformers  # Local text embeddings (RAG)
chromadb               # Local vector database (RAG)
torchvision            # Required by transformers dependency