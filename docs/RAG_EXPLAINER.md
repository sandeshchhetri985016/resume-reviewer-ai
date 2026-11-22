# 🧠 RAG — How It Works (Plain English)

## The Problem

**Before RAG**, every prompt contained ALL knowledge files dumped in:

```
KNOWLEDGE:
[entire ats_tips.txt]
[entire healthcare_keywords.txt]
[entire software_engineering.txt]
[entire resume_best_practices.txt]

RESUME:
[user's resume]
```

This wastes tokens AND irrelevant knowledge can confuse the LLM. The LLM already knows what Python and AWS are — telling it again adds nothing.

---

## The RAG Pipeline (8 Steps)

```
┌──────────────────────────────────────────────────────────────┐
│                   INDEXING (done once)                        │
│                                                              │
│  knowledge/*.txt                                             │
│       │                                                      │
│       ▼                                                      │
│  Step 1: CHUNK → heading-aware splitting                     │
│       │    - Splits at ## heading boundaries                  │
│       │    - Keeps logical sections intact                    │
│       │    - Falls back to paragraph/sentence breaks          │
│       ▼                                                      │
│  Step 2: EMBED → convert each chunk into a vector            │
│       │    (384 numbers that represent the "meaning"          │
│       │     of that chunk)                                    │
│       ▼                                                      │
│  Step 3: STORE → save vectors + text + domain metadata       │
│         in ChromaDB (local vector database)                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│               RETRIEVAL (done per query)                      │
│                                                              │
│  User resume                                                 │
│       │                                                      │
│       ▼                                                      │
│  Step 4: CLASSIFY DOMAIN → embedding similarity against      │
│         16 domain descriptions (same model, zero extra cost) │
│       │    - Returns best domain + confidence score          │
│       │    - If #1 and #2 are tied (margin < 0.03),          │
│       │      searches both domains                           │
│       ▼                                                      │
│  Step 5: EMBED QUERY → convert resume into a vector          │
│       │    (same model as Step 2)                            │
│       ▼                                                      │
│  Step 6: SEARCH → ask ChromaDB:                              │
│         "Which stored vectors in THIS domain are closest?"   │
│         → returns top 3 chunks + similarity scores           │
│       │    - Falls back to full search if domain filter      │
│       │      returns no results                              │
│       ▼                                                      │
│  Step 7: INJECT → put ONLY those 3 chunks into prompt        │
│       │    - LLM gets domain-specific guidance, not noise    │
│       ▼                                                      │
│  Step 8: LLM → model answers using relevant context          │
└──────────────────────────────────────────────────────────────┘
```

---

## What Changed: Before vs Now

| Aspect | Before (Sprint 4) | Now (Sprint 12) |
|--------|-------------------|------------------|
| **Chunking** | Character-position splits (300-500 chars) — fragments like `"view velocity (e.g.,..."` | Heading-aware: starts at `## Critical Areas to Evaluate` — clean, complete sections |
| **Classification** | None — all domains searched | Embedding-based: 16 domain descriptions, 0.69-0.90 similarity |
| **Confidence** | Single domain only | Margin-based: if #1 and #2 are tied (diff < 0.03), searches both |
| **Knowledge content** | Keyword lists (`Python, Java, AWS...`) | Recruiter guidance (`Metrics that impress, Common mistakes, Resume structure`) |
| **Fallback** | No fallback — empty results | Full ChromaDB search if domain filter returns nothing |

---

## What Each Component Does

| Component | It's NOT | It IS |
|-----------|----------|-------|
| **sentence-transformers** | An AI that understands resumes | A math function that converts text → numbers. "nurse" and "patient" get similar numbers |
| **ChromaDB** | A database that knows about ATS | A smart search engine. "Find me chunks similar to this resume" |
| **Heading-aware chunking** | Randomly cutting text | Splitting at `##` section headers so each chunk is a complete, meaningful section |
| **Domain classification** | Keyword counting | Embedding similarity — same model, zero extra cost, catches synonyms |
| **Margin check** | Just looking at the top score | Comparing #1 vs #2 — if they're close, we search both to avoid missing content |

---

## Domain Classification Explained

The classifier uses the **already-loaded embedding model** to compare the resume against 16 domain descriptions:

```
Resume text → embedder → resume vector

Domain descriptions → embedder → domain vectors (pre-computed, cached)

Cosine similarity(resume_vector, each_domain_vector) → scores

Best domain + margin → determine search scope
```

This is free because the model was already loaded for RAG. No extra API call, no extra compute.

### Why margin matters

```
healthcare: 0.7336
aged_care:  0.7192
margin:     0.0144  ← TOO CLOSE

→ Search BOTH domains
```

vs

```
software_engineering: 0.8025
data_science:         0.6683
margin:               0.1342  ← CLEAR WINNER

→ Search software_engineering only
```

---

## Knowledge Files: Why They Matter

The knowledge files were rewritten from keyword lists to **actionable recruiter guidance**.

| Before | After |
|--------|-------|
| `Python, Java, React, AWS, Docker` | "Metrics that impress: performance improvements (latency, throughput), test coverage percentages, deployment frequency, team size led" |
| `AHPRA, wound care, triage` | "Critical certifications to verify: AHPRA Registration (RN, EN, or Nurse Practitioner) — include registration number" |
| `Xero, QuickBooks, reconciliation` | "Key areas to evaluate: accounting standards (GAAP, IFRS, AASB), tax knowledge (BAS, GST, PAYG), software proficiency (Xero, MYOB)" |

The LLM already knows what Python is. What it doesn't know is what a **hiring manager** considers a strong software engineering resume. That's what the knowledge files now provide.

---

## Visual: Before vs After

### Before (static injection):
```
┌──────────────────────┐
│  knowledge/*.txt     │────┐
└──────────────────────┘    │
                            ▼
                    ┌────────────────┐
                    │  build_prompt  │───→ LLM (with ALL knowledge dumped in)
                    └────────────────┘
```

### Now (domain-filtered RAG):
```
┌──────────────────────┐    ┌────────────────┐
│  knowledge/*.txt     │───→│  ChromaDB      │ (chunked + embedded on first run)
│  18 files, 289 chunks│    └────────────────┘
└──────────────────────┘            ▲
                            query   │
                                    │
                    ┌───────────────┤
                    │               │
                    ▼               │
            ┌────────────────┐     │
            │  classify_     │     │
            │  domain()      │     │
            │  (embedding    │     │
            │   similarity)  │     │
            └───────┬────────┘     │
                    │               │
                    ▼               │
            ┌────────────────┐     │
            │  retrieve()    │─────┘
            │  (domain-      │
            │   filtered)    │
            └───────┬────────┘
                    │
                    ▼
            ┌────────────────┐
            │  build_prompt  │───→ LLM (with 3 relevant chunks only)
            └────────────────┘
```

---

## The Key Insight

**ChromaDB does NOT understand your resume.**

It only does one thing:
> "Given this query vector, find the 3 stored vectors with the highest cosine similarity."

Cosine similarity = measuring the angle between two vectors. Small angle = similar meaning. Big angle = different meaning.

That's it. No magic. No understanding. Just math.

The "intelligence" comes from:
1. The quality of your chunks (heading-aware → complete sections, not fragments)
2. The embedding model (BAAI/bge-small-en-v1.5 — captures meaning well)
3. Domain filtering (prevents irrelevant cross-domain noise)
4. The LLM (how well it uses the retrieved context)