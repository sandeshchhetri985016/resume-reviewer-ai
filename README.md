# 📄 AI Resume Assistant

> An intelligent resume analysis tool powered by AI — built with **Streamlit**, **OpenRouter (LLM)**, **RAG (Retrieval-Augmented Generation)**, and **custom scoring logic**. Upload a PDF or paste your resume to get instant feedback, ATS matching, visual dashboards, and downloadable PDF reports.

![Tech Stack](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python)
![Framework](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit)
![RAG](https://img.shields.io/badge/RAG-ChromaDB-100947?style=flat-square)
![Model](https://img.shields.io/badge/Embedding-BAAI/bge--small--en--v1.5-22c55e?style=flat-square)
![Cost](https://img.shields.io/badge/Cost-0%24-brightgreen?style=flat-square)

---

## ✨ Features

### 🔍 Two Analysis Modes
- **Resume Analysis** — holistic evaluation of skills, experience, clarity, impact, and ATS compatibility
- **ATS Job Match** — compares your resume against a job description to calculate match score, missing keywords, and targeted recommendations

### 🎨 Modern UI
- Gradient header, 4 color-coded score cards, styled feedback cards (green/amber/blue)
- Plotly gauge chart and 5-axis radar chart
- PDF download button

### 🧠 AI-Powered with RAG
- **Retrieval-Augmented Generation** using ChromaDB + sentence-transformers
- Only the **top 3 relevant knowledge chunks** are injected into the LLM prompt (not all files)
- **18 career domain files** covering healthcare, IT, trades, finance, aviation, and more
- **261 indexed chunks** for cross-domain retrieval
- Embedding model: `BAAI/bge-small-en-v1.5` (runs locally, $0 cost)

### 📊 Visual Feedback
- Score gauge (0–100) with red/amber/green ranges
- 5-axis radar chart (skills, experience, clarity, impact, ATS match)
- Breakdown expander for raw 0–10 values

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
| **Sprint Log** | Every change organized by sprint — what changed, why, and outcome | [docs/SPRINT_LOG.md](docs/SPRINT_LOG.md) |
| **User Stories** | Full Mermaid flowchart covering every user path | [docs/USER_STORY.md](docs/USER_STORY.md) |
| **RAG Explainer** | Plain-English explanation of the RAG pipeline | [docs/RAG_EXPLAINER.md](docs/RAG_EXPLAINER.md) |

---

## 🏗️ Project Structure

```
resume-reviewer/
├── app.py                    # Main Streamlit application
├── rag_engine.py             # RAG pipeline: chunking, embeddings, retrieval
├── requirements.txt          # Python dependencies
├── .env.example              # API key template (for others to copy)
├── .env                      # API key (NOT committed)
├── .gitignore
│
├── docs/                     # Portfolio documentation
│   ├── ARCHITECTURE.md       # System architecture diagram
│   ├── PRODUCT_REQUIREMENTS.md  # PRD and user stories
│   ├── TECHNICAL_BLUEPRINT.md   # Tech stack specifications
│   ├── SPRINT_LOG.md         # Development sprint history
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
│   ├── accounting.txt
│   ├── aged_care.txt
│   ├── ats_tips.txt
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
Opens at `http://localhost:8501`.

### 6. Test RAG (optional)
```bash
python rag_demo.py
```
See how cross-domain retrieval works in the terminal.

---

## 🖥️ Usage

1. Choose mode: **Resume Analysis** or **ATS Job Match**
2. Upload a PDF **or** paste your resume text
3. For ATS Match, paste the job description
4. Click **🚀 Analyze Resume**
5. View the dashboard: score cards, gauge, radar, feedback cards, breakdown
6. Download the PDF report

---

## 🧠 RAG System

The app uses **Retrieval-Augmented Generation** — only the 3 most relevant knowledge chunks are retrieved per query, rather than dumping all files into the prompt.

| Metric | Value |
|--------|-------|
| Knowledge files | 18 career domains |
| Total chunks | 261 |
| Embedding model | `BAAI/bge-small-en-v1.5` (384-dim, local) |
| Vector database | ChromaDB (local, persistent) |
| Retrieval distance | < 0.70 for all major domains |
| Cost | $0 (no paid APIs) |

**Test retrieval performance:**
```bash
python rag_demo.py
# Type: "how to become a pilot" → returns aviation content
# Type: "Java developer resume" → returns software engineering content
# Type: "plumber resume tips" → returns plumbing content
```

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
| `sentence-transformers` | Local text embeddings (RAG) |
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
| `model` | `app.py` | `openrouter/free` | OpenRouter model |

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
