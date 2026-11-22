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

## Sprint 8 — Deterministic Rubric Scoring

**Goal:** Replace LLM-dependent scoring with a transparent, weighted rubric.

### Changes
- Created `scoring.py` with 5 deterministic scoring categories:
  - Formatting (15%) — section structure, bullet points, contact info
  - ATS Readiness (20%) — keyword density, required sections, job titles
  - Experience Quality (25%) — years, roles, career progression
  - Achievement Density (20%) — quantified bullets vs total
  - Skills Relevance (20%) — keyword match, soft/hard balance
- Built regex patterns for measurable achievements (%, $, clients, team sizes, etc.)
- Added resume statistics (word count, bullet count, sections detected)
- Modified `app.py` to blend: `score = rubric × 70% + LLM × 30%`
- Added rubric breakdown expander in the UI

### Files Created
- `scoring.py`

### Files Modified
- `app.py` — integrated rubric scoring with blended score

### Outcome
✅ Scores are now deterministic and transparent — users see weighted criteria  
✅ Achievement density measured precisely with regex patterns  
✅ LLM only influences 30% of final score  

---

## Sprint 9 — ATS Gap Analysis & Knowledge File Rewrite

**Goal:** Add ATS keyword gap analysis and convert knowledge files from keyword lists to actionable recruiter guidance.

### Changes
- Added `analyze_ats_gap()` to `scoring.py` — deterministic keyword comparison
  - Extracts unigrams + bigrams from resume and job description
  - Classifies missing keywords as critical (repeated in JD) or nice-to-have
  - Returns coverage percentage, matched/missing counts
- Added ATS gap analysis UI section in `app.py`:
  - 3 color-coded metric cards (Coverage, Matched, Missing)
  - Tag cloud display for critical missing, other missing, and matched keywords
  - Actionable tips with coverage targets
- Rewrote all 16 domain knowledge files:
  - **Before:** Comma-separated keyword lists (Python, Java, React...)
  - **After:** Actionable recruiter guidance (metrics that impress, common mistakes, resume structure)
  - Examples now contain context like "Managed 12-bed ward independently" instead of raw terms
- Rebuilt RAG index: 141 chunks (down from 261, but higher quality)

### Files Modified
- `scoring.py` — added `analyze_ats_gap()` (~90 lines)
- `app.py` — ATS gap UI, import changes
- 16 knowledge files — complete content rewrite
- `chroma_db/` — rebuilt index

### Outcome
✅ ATS mode now shows users exactly which keywords they're missing  
✅ Knowledge files now provide evaluation criteria, not vocabulary  
✅ RAG adds genuine value instead of telling the LLM what it already knows  

---

## Sprint 10 — Embedding-Based Domain Classification

**Goal:** Replace keyword-based domain classifier with embedding similarity for more accurate domain detection.

### Changes
- Removed keyword-counting classifier (0.42-0.64 confidence, confused healthcare/aged_care)
- Added 16 `DOMAIN_DESCRIPTIONS` — concise descriptions of what each domain looks like
- Built `classify_domain()` method using cosine similarity against the pre-loaded embedding model
  - Zero extra cost (model already loaded for RAG)
  - Similarity scores: 0.77-0.90 (vs 0.45-0.64 before)
  - 7/7 test domains classified correctly
- Added `_domain_to_chunk_domain()` mapping to reconcile classifier names with ChromaDB metadata
- Added `domain` field to chunk metadata during indexing

### Files Modified
- `rag_engine.py` — replaced `DOMAIN_KEYWORDS` + `classify_domain()` with embedding-based version
- `chroma_db/` — rebuilt index with domain metadata

### Outcome
✅ Classification similarity jumped from 0.45-0.64 to 0.77-0.90  
✅ No more "AWS → cloud engineering" when it should be software engineering  
✅ All 16 domains now cleanly separated  

---

## Sprint 11 — Heading-Aware Chunking & Margin-Based Retrieval

**Goal:** Fix mid-sentence fragment chunks and resolve healthcare/aged_care classifier ambiguity.

### Changes
- Replaced character-position chunker with heading-aware chunker:
  - Detects `## ` heading boundaries to keep logical sections intact
  - Falls back to paragraph breaks and sentence boundaries for large sections
  - Eliminated fragments like `"view velocity (e.g.,..."` — now chunks start cleanly at `## Critical Areas to Evaluate`
- Added margin-based domain confidence:
  - If #1 and #2 domain similarities are within < 0.03, search both domains
  - This fixes healthcare vs aged_care ambiguity (0.73 vs 0.72 → both searched)
- Made rubric scoring visible by default (`expanded=True`)
- Chunks increased from 141 to 289 (each heading becomes its own chunk)

### Files Modified
- `rag_engine.py` — replaced `_chunk_text()` with heading-aware version, added margin logic
- `app.py` — changed rubric expander from `expanded=False` to `expanded=True`

### Outcome
✅ No more mid-sentence fragments — chunks start at clean heading boundaries  
✅ healthcare/aged_care ambiguity resolved via margin detection (both searched when tied)  
✅ Users now see the rubric breakdown by default — scoring transparency  

---

## Sprint 12 — Scoring Reform & Classifier Refinement

**Goal:** Remove the arbitrary 70/30 score blend, eliminate rubric dependence on demo knowledge files, and fix classification false positives.

### Changes
- Removed the 70/30 rubric + LLM score blend (was opinionated, no data justifying it)
  - Score now comes **100% from the deterministic rubric**
  - LLM now generates **feedback only** (summary, strengths, weaknesses, improvements — no score)
- Removed `normalize_score()` function (dead code after score blend removal)
- Simplified `build_prompt()` — removed score/breakdown schema, LLM no longer asked for scores
- Removed `domain_keywords` dependency from `score_skills_relevance()`:
  - Was never passed by `app.py`, always fell back to "No domain keywords provided"
  - Replaced with purely structural checks (skills section, education section, soft/hard skills balance)
- Fixed bullet character detection:
  - `●` (Unicode U+25CF) missing from `BULLET_PATTERN` and all 4 regex locations
  - Added `●` and 10 other common bullet characters to all patterns
- Fixed date range parsing:
  - En-dash `–` and em-dash `—` not matching `DATE_RANGE_PATTERN`
  - Added both dash variants to pattern
- Added model fallback retry logic:
  - OpenRouter `openrouter/free` sometimes routes to content-safety models
  - Added `FREE_MODELS` list with 3 fallback models, tried sequentially
  - Each response validated as JSON before accepting
- Suppressed transformers logging noise:
  - `logging.getLogger("transformers").setLevel(logging.ERROR)` + env vars before imports
- Fixed domain classifier false positive (multi-sector resume → construction):
  - Construction description had generic safety/management terms overlapping with healthcare
  - Replaced with trade-specific vocabulary (carpenter, bricklayer, excavator, demolition)
  - Verified: multi-sector resume now correctly → healthcare (0.691), not construction
- Expanded ATS stop words to filter JD filler words:
  - JD conversational phrases ("tech-savvy", "full-time", "currently employed") were splitting into junk keywords
  - Added 8 filler words to `STOP_WORDS`: savvy, work, time, employed, full, conversion, support, currently
  - ATS keyword extraction now produces meaningful terms instead of common English filler
- Added ATS gap analysis console logging:
  - `log_section("ATS GAP ANALYSIS STARTED")` + coverage/match/missing counts
  - Makes ATS results visible in terminal for debugging

### Files Modified
- `app.py` — removed 70/30 blend, simplified prompt, added model retry loop, suppressed noise, added ATS logging
- `scoring.py` — removed `domain_keywords` param, fixed bullet regexes, fixed date regex, expanded stop words, added ATS logging call
- `rag_engine.py` — updated construction domain description

### Outcome
✅ Score is fully deterministic — reproducible, defensible, no AI influence  
✅ LLM provides feedback only — if it fails, the score still works  
✅ Bullets with `●` now detected correctly  
✅ Date ranges with en-dash/em-dash now parse  
✅ OpenRouter content-safety routing handled gracefully  
✅ Transformers noise suppressed  
✅ Multi-sector resumes no longer falsely classified as construction  
✅ ATS keywords filtered better — fewer filler words in missing/matched lists  
✅ ATS analysis logged to console for debugging

---

## Current Project Metrics

| Metric | Value |
|--------|-------|
| Total sprints | 12 |
| Knowledge files | 18 |
| Total chunks | 289 |
| Embedding model | BAAI/bge-small-en-v1.5 |
| Domain classifier | Embedding-based (16 descriptions, 0.69-0.90 similarity) |
| Chunking | Heading-aware (## boundaries) |
| Vector DB | ChromaDB (local) |
| LLM provider | OpenRouter (free tier, with model fallback) |
| UI framework | Streamlit |
| Visualization | Plotly (gauge + radar) |
| PDF generation | ReportLab |
| Scoring | Deterministic weighted rubric (100%) — no AI involvement |
| ATS analysis | Deterministic keyword gap with coverage % |

---

## Future Sprint Ideas

| Sprint | Description | Priority |
|--------|-------------|----------|
| 13 | Add reranking with cross-encoder for improved retrieval quality | High |
| 14 | Add hybrid search (BM25 + embeddings) for better non-domain queries | Medium |
| 15 | Add resume rewrite suggestions (before/after examples) | Medium |
| 16 | Improve ATS coverage with per-category scoring (Tech Tools Certs) | Medium |
| 17 | Test against 20+ real-world messy resumes (operations co-ordinator, hybrid roles) | High |
| 18 | Expand knowledge base to 30+ career files | Low |
| 19 | Add authentication and user history | Low |