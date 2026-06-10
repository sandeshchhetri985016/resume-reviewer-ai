# 🧠 RAG — How It Works (Plain English)

## The Problem

**Before RAG**, every prompt contained ALL knowledge files dumped in:

```
KNOWLEDGE:
[entire ats_tips.txt]
[entire healthcare_keywords.txt]
[entire resume_best_practices.txt]

RESUME:
[user's resume]
```

This wastes tokens AND irrelevant knowledge can confuse the LLM.

---

## The RAG Pipeline (7 Steps)

```
┌─────────────────────────────────────────────────────────┐
│                   INDEXING (done once)                   │
│                                                         │
│  knowledge/*.txt                                          │
│       │                                                  │
│       ▼                                                  │
│  Step 1: CHUNK → split files into small pieces           │
│       │    (200-500 chars each, with overlap)             │
│       ▼                                                  │
│  Step 2: EMBED → convert each chunk into a vector        │
│       │    (a list of ~384 numbers that represent         │
│       │     the "meaning" of that chunk)                  │
│       ▼                                                  │
│  Step 3: STORE → save vectors + text in ChromaDB         │
│         (a local database designed for vectors)           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  RETRIEVAL (done per query)               │
│                                                          │
│  User resume + question                                   │
│       │                                                  │
│       ▼                                                  │
│  Step 4: EMBED QUERY → convert the question into         │
│         a vector (same model as Step 2)                   │
│       │                                                  │
│       ▼                                                  │
│  Step 5: SEARCH → ask ChromaDB:                          │
│         "Which stored vectors are closest to this?"       │
│         → returns top 3 chunks + similarity scores       │
│       │                                                  │
│       ▼                                                  │
│  Step 6: INJECT → put ONLY those 3 chunks into prompt    │
│       │                                                  │
│       ▼                                                  │
│  Step 7: LLM → model answers using only relevant context  │
└─────────────────────────────────────────────────────────┘
```

---

## What Each Component Does

| Component | It's NOT | It IS |
|-----------|----------|-------|
| **sentence-transformers** | An AI that understands resumes | A math function that converts text → numbers (embeddings). "dog" and "puppy" get similar numbers |
| **ChromaDB** | A database that knows about ATS | A smart search engine. "Find me chunks similar to this resume" |
| **Chunking** | Randomly cutting text | Splitting at logical boundaries (paragraphs, sentences) with 50-char overlap so nothing is lost between cuts |

---

## Why This Is Better

| Aspect | Before (static injection) | After (RAG) |
|--------|--------------------------|-------------|
| Tokens used | ALL knowledge files every time | Only 3 most relevant chunks |
| Relevance | ATS tips go into every prompt even for non-ATS questions | Only contextually similar content |
| Scalability | Add 50 files → prompt becomes enormous | Add 500 files → retrieval still fast |
| Accuracy | LLM has to sift through noise | LLM gets focused, relevant context |

---

## The Key Insight

**ChromaDB does NOT understand your resume.**

It only does one thing:
> "Given this query vector, find the 3 stored vectors with the highest cosine similarity."

Cosine similarity = measuring the angle between two vectors. Small angle = similar meaning. Big angle = different meaning.

That's it. No magic. No understanding. Just math.

The "intelligence" comes from:
1. The quality of your chunks (how well they're split)
2. The embedding model (how well it captures meaning as numbers)
3. The LLM (how well it uses the retrieved context)

---

## Visual: Before vs After

### Before (current):
```
┌──────────────────────┐
│  knowledge/*.txt     │────┐
└──────────────────────┘    │
                            ▼
                    ┌────────────────┐
                    │  build_prompt  │───→ LLM (with ALL knowledge dumped in)
                    └────────────────┘
```

### After (RAG):
```
┌──────────────────────┐    ┌────────────────┐
│  knowledge/*.txt     │───→│  ChromaDB      │ (chunked + embedded on first run)
└──────────────────────┘    └────────────────┘
                                    ▲
                            query   │
                            ────────┘
                       
                    ┌────────────────┐
                    │  retrieve()    │───→ top 3 relevant chunks
                    └────────────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │  build_prompt  │───→ LLM (with ONLY 3 relevant chunks)
                    └────────────────┘
```

---

## What You Will Build

1. `rag_engine.py` — a class with `retrieve(text, top_k=3)` that returns relevant chunks
2. `rag_demo.py` — a terminal script to test retrieval without the UI
3. Modified `app.py` — call `rag_engine.retrieve(resume)` instead of `load_knowledge()`

---

## Test Your Understanding

After reading this, you should be able to answer:

1. What is an embedding? (one sentence)
2. What does ChromaDB return when you search it?
3. Why do we chunk files instead of embedding the whole file?
4. What happens if chunks are too large?
5. What happens if chunks are too small?

If you can answer these, you understand RAG enough to build it.