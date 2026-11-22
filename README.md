# 📄 AI Resume Assistant

> An intelligent resume analysis tool powered by AI — built with **Streamlit**, **OpenRouter (LLM)**, **RAG (Retrieval-Augmented Generation)**, and **deterministic scoring**. Upload a PDF or paste your resume to get instant feedback, ATS keyword gap analysis, visual dashboards, and downloadable PDF reports.

![Tech Stack](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python)
![Framework](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit)
![RAG](https://img.shields.io/badge/RAG-ChromaDB-100947?style=flat-square)
![Model](https://img.shields.io/badge/Embedding-BAAI/bge--small--en--v1.5-22c55e?style=flat-square)
![Cost](https://img.shields.io/badge/Cost-0%24-brightgreen?style=flat-square)

---

## ✨ Features

### 🔍 Two Analysis Modes
- **Resume Analysis** — holistic evaluation of skills, experience, clarity, impact, and ATS compatibility
- **ATS Job Match** — compares your resume against a job description with **concept-level + keyword + semantic gap analysis** showing exactly which skills and keywords are missing

### 📊 Deterministic Scoring (No LLM Bias)
- **Weighted rubric** with 5 categories: Formatting (15%), ATS Readiness (20%), Experience Quality (25%), Achievement Density (20%), Skills Relevance (20%)
- **Single canonical Job Fit Score (0-100)** — fuses concept coverage, semantic alignment, and evidence strength with role-adaptive weights
- **Separate Resume Quality score** — deterministic rubric kept distinct from job relevance
- **LLM provides feedback only** — summary, strengths, weaknesses, improvements (no score)
- **Rubric breakdown visible by default** — users see exactly how their score is calculated
- **ATS keyword gap analysis** — console-logged for debugging, stop-word filtered for cleaner results

### 🧠 AI-Powered with Domain-Aware RAG
- **Embedding-based domain classification** — detects the resume's industry using the same model (zero extra cost)
- **Margin-based confidence** — if two domains are nearly tied (diff < 0.03), searches both
- **Heading-aware chunking** — splits at `##` boundaries so chunks are complete, meaningful sections
- **18 career domain files** with actionable recruiter guidance (not keyword lists)
- **289 indexed chunks** for cross-domain retrieval
- **Model retry logic** — tries 3 free models sequentially, validates JSON before accepting

### 🔍 Multi-Layer ATS Analysis
- **Keyword Coverage** — exact token overlap (transparent, bonus-only)
- **Concept Coverage** — ontology-based normalized skill matching (~40 concepts)
- **Semantic Equivalences** — BGE phrase-level matches shown as AI-understood equivalences
- **Effective coverage** includes semantically bridged gaps
- **Critical missing keywords** (repeated in JD) highlighted in red
- **Other missing keywords** shown in amber with actionable tips

### 🎨 Modern UI
- Gradient header, 4 color-coded score cards, styled feedback cards (green/amber/blue)
- Plotly gauge chart and 5-axis radar chart
- Rubric breakdown visible by default for scoring transparency
- PDF download button

### 📄 PDF Report Export
- Downloadable PDF with score, summary, strengths, weaknesses, and improvements
- Built with ReportLab

---

## 📋 Documentation

| Document | Description | Link |
|----------|-------------|------|
| **Product Requirements** | Problem statement, user stories, functional requirements | [docs/PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md) |
| **Technical Blueprint** | Tech stack, project structure, data flow, API contract | [docs/TECHNICAL_BLUEPRINT.md](docs/TECHNICAL_BLUEPRINT.md) |
| **Architecture** | System architecture diagram, component dependencies | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Sprint Log** | 12 sprints documented — what changed, why, and outcome | [docs/SPRINT_LOG.md](docs/SPRINT_LOG.md) |
| **User Stories** | Full Mermaid flowchart covering every user path | [docs/USER_STORY.md](docs/USER_STORY.md) |
| **RAG Explainer** | Plain-English explanation of the RAG pipeline | [docs/RAG_EXPLAINER.md](docs/RAG_EXPLAINER.md) |

---

## 🏗️ Project Structure

```
resume-reviewer/
├── app.py                    # Main Streamlit application
├── rag_engine.py             # RAG pipeline: chunking, embeddings, domain classification, retrieval
├── scoring.py                # Deterministic rubric scoring + ATS gap analysis
├── requirements.txt          # Python dependencies
├── .env.example              # API key template (for others to copy)
├── .env                      # API key (NOT committed)
├── .gitignore
│
├── docs/                     # Portfolio documentation
│   ├── ARCHITECTURE.md       # System architecture diagram
│   ├── PRODUCT_REQUIREMENTS.md  # PRD and user stories
│   ├── TECHNICAL_BLUEPRINT.md   # Tech stack specifications
│   ├── SPRINT_LOG.md         # Development sprint history (12 sprints)
│   ├── USER_STORY.md         # User interaction flowcharts
│   └── RAG_EXPLAINER.md      # RAG pipeline explanation
│
├── scripts/                  # Utility scripts (not app code)
│   └── rag_demo.py           # Terminal RAG pipeline demo
│
├── archive/                  # Legacy code (not used in current app)
│   ├── main.py               # CLI-only resume analysis
│   ├── validators.py         # JSON schema validation (legacy)
│   └── scoring_engine.py     # Local keyword scoring (legacy)
│
├── knowledge/                # Career domain knowledge files for RAG
│   ├── accounting.txt        # Each file contains actionable recruiter guidance
│   ├── aged_care.txt         # (what metrics impress, common mistakes, etc.)
│   ├── ats_tips.txt          # — NOT keyword lists. Actual evaluation criteria.
│   ├── aviation.txt
│   ├── cloud_engineering.txt
│   ├── construction.txt
│   ├── cyber_security.txt
│   ├── data_science.txt
│   ├── electrician.txt
│   ├── healthcare_keywords.txt
│   ├── hr.txt
│   ├── logistics.txt
│   ├── marketing.txt
│   ├── mobile_development.txt
│   ├── nursing.txt
│   ├── plumber.txt
│   ├── resume_best_practices.txt
│   └── software_engineering.txt
│
└── chroma_db/                # Local vector database (auto-created)
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- An [OpenRouter](https://openrouter.ai) API key (free, no credit card required)

### 1. Clone the repository
```bash
git clone https://github.com/sandeshchhetri985016/resume-reviewer-ai.git
cd resume-reviewer-ai
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your API key
Create a `.env` file in the project root:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
```

### 5. Run the app
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`. First run will index the knowledge files (~5 seconds).

### 6. Test RAG (optional)
```bash
python scripts/rag_demo.py
```
See how cross-domain retrieval works in the terminal.

---

## � Deployment

### Quick Deploy to Cloud (Free Tier)

**Option 1: Railway (Recommended)**
- Fastest setup. Auto-detects Dockerfile.
- Go to https://railway.app → New Project → Deploy from GitHub
- Add `OPENROUTER_API_KEY` in Variables
- App is live in ~2 minutes

**Option 2: Render**
- Also supports Docker
- Go to https://render.com → New Web Service → Connect repo

**Option 3: Local Docker**
```bash
docker-compose up
# App at http://localhost:8501
```

See **[Deployment Guide](docs/DEPLOYMENT.md)** for step-by-step instructions.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[Deployment Guide](docs/DEPLOYMENT.md)** | Deploy to Railway/Render (free tier) — **START HERE** |
| **[Troubleshooting](docs/TROUBLESHOOTING.md)** | Common issues & fixes |
| **[Product Requirements](docs/PRODUCT_REQUIREMENTS.md)** | Features & requirements |
| **[Technical Blueprint](docs/TECHNICAL_BLUEPRINT.md)** | Tech stack & architecture |
| **[Sprint Log](docs/SPRINT_LOG.md)** | Development history |

---

## �🖥️ Usage

1. Choose mode: **Resume Analysis** or **ATS Job Match**
2. Upload a PDF **or** paste your resume text
3. For ATS Match, paste the job description
4. Click **🚀 Analyze Resume**
5. View the dashboard:
   - Score cards (Overall, ATS, Formatting, Achievements)
   - Score gauge and radar chart
   - **Rubric breakdown** showing how each category scored
   - Strengths, weaknesses, improvements (styled cards)
   - **ATS keyword gap analysis** with missing keywords (if ATS mode)
6. Download the PDF report

---

## 🧠 RAG System

The app uses **domain-aware Retrieval-Augmented Generation** — only the 3 most relevant knowledge chunks are retrieved per query, filtered by detected domain.

| Metric | Value |
|--------|-------|
| Knowledge files | 18 career domains |
| Total chunks | 289 |
| Embedding model | `BAAI/bge-small-en-v1.5` (384-dim, local) |
| Vector database | ChromaDB (local, persistent) |
| Domain classifier | Embedding-based (16 descriptions, 0.69-0.90 similarity) |
| Chunking | Heading-aware (splits at `##` boundaries) |
| Confidence | Margin-based (searches both domains when tied) |
| Model fallback | 3-model retry with JSON validation |
| Cost | $0 (no paid APIs) |

**Test retrieval performance:**
```bash
python scripts/rag_demo.py
# Type: "how to become a pilot" → returns aviation content
# Type: "Java developer resume" → returns software engineering content
# Type: "plumber resume tips" → returns plumbing content
```

---

## 📊 Scoring System

### Resume Quality (Structural)
Purely deterministic rubric — no AI involvement.

| Category | Weight | Criteria |
|----------|--------|----------|
| Formatting | 15% | Sections, bullets, contact info |
| ATS Readiness | 20% | Keyword density, required sections, job titles |
| Experience Quality | 25% | Years, roles, progression, date consistency |
| Achievement Density | 20% | Quantified bullets, action verbs, bullet length |
| Skills Relevance | 20% | Skills section, education, soft/hard balance |

### Job Fit Score (JD-specific, canonical)
Single authoritative number fusing three non-overlapping layers:

| Layer | Weight (avg) | Description |
|-------|--------------|-------------|
| Concept Coverage | ~50% | Ontology-based skill matching (primary) |
| Semantic Alignment | ~25% | Per-skill BGE phrase similarity (explanation) |
| Evidence Strength | ~25% | Exact keyword overlap (bonus-only) |

Weights are role-adaptive: IT_SUPPORT emphasizes concepts, SOFTWARE_ENGINEER emphasizes semantics.

The rubric breakdown is **visible by default** so users understand exactly how their score was calculated.

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `openai` | OpenRouter API client |
| `python-dotenv` | Load `.env` variables |
| `pypdf` | PDF text extraction |
| `plotly` | Charts (gauge + radar) |
| `reportlab` | PDF report generation |
| `sentence-transformers` | Local text embeddings (RAG + domain classification) |
| `chromadb` | Local vector database (RAG) |
| `torchvision` | Required by transformers dependency |

---

## ⚙️ Configuration

| Variable | Location | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `.env` | None | OpenRouter API key |
| `EMBEDDING_MODEL_NAME` | `rag_engine.py` | `BAAI/bge-small-en-v1.5` | sentence-transformers model |
| `CHUNK_MIN_CHARS` | `rag_engine.py` | 300 | Minimum chunk size |
| `CHUNK_MAX_CHARS` | `rag_engine.py` | 500 | Maximum chunk size |
| `CHUNK_OVERLAP` | `rag_engine.py` | 50 | Chunk overlap |
| `RETRIEVE_TOP_K` | `rag_engine.py` | 3 | Chunks per query |
| `FREE_MODELS` | `app.py` | 3 models | Model retry fallback list |
| `DOMAIN_DESCRIPTIONS` | `rag_engine.py` | 16 domains | Embedding-based domain classifier |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
