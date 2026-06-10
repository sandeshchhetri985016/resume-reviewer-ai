# Sprint Log — AI Resume Assistant

> This log documents every development sprint, what changed, and why. Useful for portfolio review and understanding the project's evolution.

---

## Sprint 1 — Initial Prototype (MVP)

**Goal:** Build a working Streamlit app that calls OpenRouter and displays resume analysis results.

### Changes
- Created `app.py` with basic Streamlit UI
- Added PDF upload (PyPDF) and text paste input
- Built prompt construction with strict JSON schema rules
- Integrated OpenRouter API via OpenAI SDK
- Added basic JSON parsing with regex fallback
- Created simple metric display (score, ATS match, clarity)
- Added `main.py` for CLI-only resume analysis
- Added `validators.py` for JSON schema validation
- Added `scoring_engine.py` with healthcare keyword matching

### Files Created
- `app.py`, `main.py`, `validators.py`, `scoring_engine.py`
- `requirements.txt`, `.gitignore`
- `knowledge/ats_tips.txt`, `knowledge/healthcare_keywords.txt`, `knowledge/resume_best_practices.txt`

### Outcome
✅ Functional app — user can paste a resume, get a score and feedback  
❌ Static knowledge injection (ALL files dumped into every prompt)  
❌ Basic UI with no styling  

---

## Sprint 2 — UI Overhaul & Visualizations

**Goal:** Make the app visually attractive and add data visualizations.

### Changes
- Replaced static metric display with 4 color-coded score cards (Overall, ATS, Clarity, Skills)
- Added Plotly score gauge (0-100 with red/amber/green ranges)
- Added Plotly 5-axis radar chart
- Replaced raw Python list output with styled HTML feedback cards (green=strengths, amber=weaknesses, blue=improvements)
- Added gradient header banner with custom CSS
- Added summary callout box
- Added loading spinner during API calls
- Expanded to full-width layout (removed center column restriction)
- Added breakdown expander showing raw 0-10 values

### Files Modified
- `app.py` — major rewrite of UI section

### Outcome
✅ Professional-looking UI with proper visual hierarchy  
✅ Users can see scores at a glance  

---

## Sprint 3 — Bug Fixes & Stabilization

**Goal:** Fix crashes, deprecation warnings, and edge cases.

### Changes
- Added null guard for `raw_output` (fixes crash when model returns image instead of text)
- Replaced deprecated `use_container_width=True` with `width='stretch'` (2 occurrences)
- Installed `torchvision` to suppress noisy path warnings from `transformers` library
- Added `warnings.filterwarnings` for transformers path inspection noise
- Removed duplicate `normalize_score()` call
- Added score calibration guidelines to prompt (prevents inflated scores)
- Added `RESPONSE QUALITY` instructions (requires complete sentences, not single words)

### Files Modified
- `app.py` — bug fixes, prompt improvements
- `requirements.txt` — added `torchvision`

### Outcome
✅ No more crashes on null responses  
✅ No deprecation warnings  
✅ Feedback now requires complete sentences  

---

## Sprint 4 — RAG Pipeline Implementation

**Goal:** Replace static knowledge injection with proper Retrieval-Augmented Generation.

### Changes
- Created `rag_engine.py` with full RAG pipeline:
  - Chunking (200-500 chars with 50-char overlap, sentence/paragraph boundaries)
  - Embedding via `all-MiniLM-L6-v2` (later upgraded to `BAAI/bge-small-en-v1.5`)
  - ChromaDB persistent vector storage
  - Content-hash change detection (only re-indexes modified files)
  - Retrieval with distance score logging
- Created `rag_demo.py` for terminal-based RAG testing
- Created `RAG_EXPLAINER.md` with plain-English pipeline explanation
- Modified `app.py` to use `rag_engine.retrieve(resume)` instead of `load_knowledge()`
- Added `@st.cache_resource` for singleton RAG engine initialization

### Files Created
- `rag_engine.py`, `rag_demo.py`, `RAG_EXPLAINER.md`

### Files Modified
- `app.py` — replaced `load_knowledge()` with RAG retrieval

### Outcome
✅ RAG is working — only top 3 relevant chunks injected into prompt  
✅ Change detection prevents unnecessary re-indexing  
✅ Terminal demo available for isolated testing  

---

## Sprint 5 — Cross-Domain Knowledge Expansion

**Goal:** Expand from 3 knowledge files to 18 career domains for multi-domain RAG testing.

### Changes
- Fixed `rag_engine.py` glob: `"*.txt"` → `"**/*.txt"` to support subdirectories
- Added 13 new career domain files (initially thin, 200-650 bytes each):
  - `data_science.txt`, `cloud_engineering.txt`, `nursing.txt`, `cyber_security.txt`
  - `marketing.txt`, `hr.txt`, `accounting.txt`, `construction.txt`
  - `electrician.txt`, `plumber.txt`, `logistics.txt`, `aged_care.txt`
  - `mobile_development.txt`

### Files Created
- 13 new `.txt` files in `knowledge/`

### Files Modified
- `rag_engine.py` — glob pattern

### Outcome
✅ 18 knowledge files (up from 3)  
✅ 120 chunks (up from 74)  
✅ Cross-domain retrieval tests working (pilot → aviation, plumber → plumbing)  

---

## Sprint 6 — Documentation & Portfolio Readiness

**Goal:** Create comprehensive documentation for portfolio presentation.

### Changes
- Created `USER_STORY.md` with full Mermaid flowchart covering all user paths
- Created `PRODUCT_REQUIREMENTS.md` with PRD, user stories, functional requirements
- Created `TECHNICAL_BLUEPRINT.md` with tech stack, data flow, API contract
- Created `docs/ARCHITECTURE.md` with system architecture diagram
- Created `docs/SPRINT_LOG.md` (this file) documenting all sprints

### Tech Improvements
- Upgraded embedding model: `all-MiniLM-L6-v2` → `BAAI/bge-small-en-v1.5` (better quality)
- Increased `CHUNK_MIN_CHARS` from 200 → 300 (reduced boundary artifacts)
- Expanded all 13 thin knowledge files to 4,000-12,000 bytes each (261 total chunks)
- Index rebuilt and retrieval verified (plumber query distance improved from 1.05 → 0.56)
- Added `.gitignore` entries for `chroma_db/`, `nul`

### Files Created
- `USER_STORY.md`, `PRODUCT_REQUIREMENTS.md`, `TECHNICAL_BLUEPRINT.md`
- `docs/ARCHITECTURE.md`, `docs/SPRINT_LOG.md`
- All 13 domain knowledge files (expanded from thin to detailed)

### Files Modified
- `rag_engine.py` — embedding model + chunk size config
- 13 knowledge files — expanded with comprehensive content

### Outcome
✅ Portfolio-ready documentation covering PRD, tech stack, architecture, and sprint history  
✅ Top-tier retrieval quality (distances < 0.70 for all major domains)  
✅ 261 chunks across 18 career domains  

---

## Sprint 7 — File Reorganization

**Goal:** Clean up project root, organize all docs into `docs/`, move legacy code to `archive/`.

### Changes
- Moved all documentation to `docs/` folder (6 files)
- Moved legacy code to `archive/` folder: `main.py`, `validators.py`, `scoring_engine.py`
- Moved `rag_demo.py` to `scripts/`
- Removed junk files: `cloudflared.deb`, `nul`, `resume_app.log`
- Created `.env.example` for easy onboarding
- Updated `README.md` with correct project structure and documentation links
- Updated `docs/TECHNICAL_BLUEPRINT.md` project structure section
- Updated `.gitignore` to exclude `chroma_db/`, `nul`

### Files Moved
- `USER_STORY.md`, `PRODUCT_REQUIREMENTS.md`, `TECHNICAL_BLUEPRINT.md`, `RAG_EXPLAINER.md` → `docs/`
- `main.py`, `validators.py`, `scoring_engine.py` → `archive/`
- `rag_demo.py` → `scripts/`

### Files Removed
- `cloudflared.deb` (random binary)
- `resume_app.log` (log file)
- `nul` (Windows artifact)

### Files Created
- `.env.example`

### Outcome
✅ Clean root directory (only 5 files + folders)
✅ All documentation in `docs/` (6 files)
✅ Legacy code preserved in `archive/` (3 files)
✅ Portfolio-ready structure

---

## Current Project Metrics

| Metric | Value |
|--------|-------|
| Total sprints | 7 |
| Knowledge files | 18 |
| Total chunks | 261 |
| Total knowledge size | ~107 KB |
| Embedding model | BAAI/bge-small-en-v1.5 |
| Vector DB | ChromaDB (local) |
| Best retrieval distance | 0.45 (data science) |
| LLM provider | OpenRouter (free tier) |
| UI framework | Streamlit |
| Visualization | Plotly (gauge + radar) |
| PDF generation | ReportLab |

---

## Future Sprint Ideas

| Sprint | Description | Priority |
|--------|-------------|----------|
| 8 | Add reranking with cross-encoder for improved retrieval quality | High |
| 9 | Add query routing — detect query domain and filter ChromaDB results | Medium |
| 10 | Add hybrid search (BM25 + embeddings) for better non-domain queries | Medium |
| 11 | Expand knowledge base to 30+ career files | Low |
| 12 | Add authentication and user history | Low |
