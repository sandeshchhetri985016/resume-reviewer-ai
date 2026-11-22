# Product Requirements Document — AI Resume Assistant

## 1. Product Overview

**Product Name:** AI Resume Assistant  
**Tagline:** Resume analysis · ATS matching · AI feedback for career growth  
**Target Users:** Job seekers preparing resumes for ATS screening, career changers, and professionals seeking resume improvement feedback  
**Platform:** Web application (Streamlit)

## 2. Problem Statement

Job seekers face three challenges:
1. **ATS rejection**: 75% of resumes are rejected by Applicant Tracking Systems before a human reads them. Most candidates don't know why their resume failed.
2. **Inconsistent feedback**: Getting quality feedback on a resume requires paying a professional or relying on subjective opinions.
3. **Domain mismatch**: Generic resume advice doesn't account for industry-specific keywords, especially in regulated sectors like healthcare, IT, and trades.

## 3. Target Audience

| Persona | Needs | Pain Points |
|---------|-------|-------------|
| Entry-level job seeker | First resume, no experience | Weak keyword density, poor formatting |
| Career changer | Transferable skills highlighting | Old resume mismatches new industry keywords |
| Experienced professional | Quantified achievements, ATS optimization | Overconfidence in outdated formats |
| Recruiter (secondary) | Quick candidate resume screening | Time-consuming manual review |

## 4. User Stories

### Must-Have (MVP)
- As a user, I can upload a PDF resume or paste text so the system can analyze it
- As a user, I can choose between "Resume Analysis" and "ATS Job Match" modes
- As a user, I receive a score (0-100) and breakdown of my resume quality
- As a user, I see specific strengths, weaknesses, and improvements
- As a user, I can visualize my resume score with a gauge chart and radar chart
- As a user, I can download a PDF report of the analysis
- As a user, I want the scoring to be transparent — I can see the weighted rubric breakdown

### Should-Have
- As a user, I want domain-specific knowledge to influence the analysis (RAG)
- As a user, I want the feedback to be detailed sentences, not single words
- As a user, I want consistent scoring across different resume types
- As a user, I want the system to automatically detect my industry and filter knowledge accordingly (embedding-based domain classification)
- As a user, in ATS mode I want to see exactly which keywords I'm missing from the job description

### Could-Have
- As a user, I want reranking for improved retrieval relevance
- As a user, I can compare two resumes side by side
- As a user, I want before/after rewrite suggestions for weak resume sections

## 5. Functional Requirements

| FR ID | Description | Priority |
|-------|-------------|----------|
| FR1 | System accepts PDF upload (max 200MB) | P0 |
| FR2 | System accepts pasted text input | P0 |
| FR3 | System provides two analysis modes (Resume Analysis, ATS Job Match) | P0 |
| FR4 | System calls OpenRouter API with structured prompt | P0 |
| FR5 | System parses JSON response and normalizes score | P0 |
| FR6 | System renders score gauge (0-100) using Plotly | P0 |
| FR7 | System renders 5-axis radar chart using Plotly | P0 |
| FR8 | System generates downloadable PDF report using ReportLab | P0 |
| FR9 | System indexes knowledge files into ChromaDB via RAG pipeline | P1 |
| FR10 | System retrieves only relevant chunks per query (not all files) | P1 |
| FR11 | System suppresses noisy transformer warnings | P1 |
| FR12 | System enforces response quality (sentence-level feedback) | P1 |
| FR13 | System supports cross-domain knowledge (18 career files) | P2 |

## 6. Non-Functional Requirements

| NFR ID | Description | Target |
|--------|-------------|--------|
| NFR1 | Embedding model loads within 5 seconds | < 5s |
| NFR2 | API response time | < 30s |
| NFR3 | ChromaDB index persistence across sessions | Yes |
| NFR4 | Cost: $0 (fully free stack) | Yes |
| NFR5 | Embedding model: BAAI/bge-small-en-v1.5 | 384-dim, local |
| NFR6 | Vector DB: ChromaDB (local, no server) | Persistent |

## 7. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Knowledge chunks | 289 | 500+ |
| Knowledge domains | 18 | 30+ |
| Retrieval distance (< 0.70 = good) | ~0.56 for plumber query | < 0.70 for all domains |
| Domain classifier accuracy | 0.69-0.90 similarity, no false positives | < 0.03 margin triggers top-2 search |
| Scoring | 100% deterministic rubric (no AI) | Maintain |
| ATS model fallback | 3 model retry loop | Auto-recover from content-safety routing |
| Reranking | Not implemented | Cross-encoder v2 |

## 8. Scope

### In Scope
- Single-user Streamlit web app
- OpenRouter API integration (free models)
- RAG with local ChromaDB + sentence-transformers
- 18 career domain knowledge files
- PDF report generation
- Custom CSS styling

### Out of Scope
- Multi-user authentication
- User accounts or saved history
- Cloud deployment (local only, Cloudflare tunnel optional)
- Hybrid search (BM25 + embeddings)
- Real-time collaborative editing