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
│  │  │  _chunk_text()                  │                        │    │
│  │  │  - 300-500 chars per chunk     │                        │    │
│  │  │  - 50 char overlap             │                        │    │
│  │  │  - Sentence/paragraph breaks   │                        │    │
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
│  │  └─────────────────────────────────┘                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Retrieval Pipeline (per query)                              │    │
│  │                                                             │    │
│  │  Resume text ──▶ embed query ──▶ ChromaDB query ──▶ top 3    │    │
│  │                    (same model)   (cosine sim)    chunks    │    │
│  │                                                             │    │
│  │  Returns: concatenated string of top 3 chunks              │    │
│  │  Fallback: "No specific knowledge chunks matched..."        │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Dependencies

```
app.py
  ├── rag_engine.py
  │     ├── sentence-transformers (embeddings)
  │     └── chromadb (vector storage)
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
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Streamlit instead of Flask/Django** | No HTML/CSS/JS needed; built-in widgets for file upload, text areas, metrics |
| **ChromaDB instead of Pinecone/Weaviate** | 100% free, no server, file-based persistence |
| **BAAI/bge-small-en-v1.5 instead of OpenAI embeddings** | Zero API cost, runs locally, no data leaves machine |
| **OpenRouter instead of direct OpenAI** | Free tier available, multiple model options, no credit card needed |
| **RAG instead of static knowledge injection** | Token-efficient, scalable to 500+ files, contextually relevant |
| **openrouter/free instead of fixed model** | Auto-routes to available capacity; avoids paid API calls |
| **Prompt-based response quality enforcement** | Free (no second model needed for reranking) |