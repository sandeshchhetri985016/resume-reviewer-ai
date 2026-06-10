"""
rag_engine.py — RAG (Retrieval-Augmented Generation) for Resume Reviewer

What this does:
1. Reads all .txt files from the knowledge/ directory
2. Splits them into overlapping chunks (200-500 chars)
3. Converts each chunk into a vector embedding (384 numbers)
4. Stores vectors in a local ChromaDB database
5. At query time, embeds the query and finds the most similar chunks
6. Returns only those relevant chunks to be injected into the LLM prompt

This replaces the old load_knowledge() which dumped ALL files verbatim.
"""

import os
import re
import hashlib
from pathlib import Path

# ---------------------------------------------------------------------------
# These are 100% free, local packages. No API keys, no accounts, no trials.
# sentence-transformers: converts text to vectors on your CPU
# chromadb:            local vector database (stores data in ./chroma_db/)
# ---------------------------------------------------------------------------

# Lazy imports — user will be prompted to install if missing
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None


# ---------------------------------------------------------------------------
# Configuration — tweak these to experiment
# ---------------------------------------------------------------------------
KNOWLEDGE_DIR = Path("knowledge")
CHROMA_DB_DIR = Path("chroma_db")
COLLECTION_NAME = "resume_knowledge"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5" # Better quality than MiniLM, same speed
CHUNK_MIN_CHARS = 300                           # Minimum characters per chunk
CHUNK_MAX_CHARS = 500                           # Maximum characters per chunk
CHUNK_OVERLAP = 50                              # Overlap between consecutive chunks
RETRIEVE_TOP_K = 3                              # Number of chunks to return per query


class RagEngine:
    """
    A minimal RAG engine.

    Usage:
        engine = RagEngine()
        engine.build_index()          # Run once to index all knowledge files
        chunks = engine.retrieve("resume for aged care")  # Get top 3 relevant chunks
        prompt = f"Context:\\n{chunks}\\n\\nResume:\\n{resume}"
    """

    def __init__(self):
        """Set up the embedding model and ChromaDB client."""
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is not installed.\n"
                "Run: pip install sentence-transformers"
            )
        if chromadb is None:
            raise ImportError(
                "chromadb is not installed.\n"
                "Run: pip install chromadb"
            )

        # Step A: Load the embedding model (downloads ~80 MB on first run)
        # all-MiniLM-L6-v2 creates 384-dimensional vectors.
        print("[RAG] Loading embedding model:", EMBEDDING_MODEL_NAME)
        self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("[RAG] Model loaded successfully.")

        # Step B: Connect to ChromaDB (creates ./chroma_db/ directory on first run)
        # Settings(anonymized_telemetry=False) disables the telemetry prompt.
        CHROMA_DB_DIR.mkdir(exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

        # Step C: Get or create the collection
        # A collection is like a "table" for vectors.
        try:
            self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
            print(f"[RAG] Found existing collection '{COLLECTION_NAME}' "
                  f"with {self.collection.count()} chunks.")
        except Exception:
            self.collection = self.chroma_client.create_collection(COLLECTION_NAME)
            print(f"[RAG] Created new collection '{COLLECTION_NAME}'.")

        # Step D: Track which files have been indexed (by content hash)
        self.indexed_files = set()
        if self.collection.count() > 0:
            # Read metadata from ChromaDB to know which files were indexed
            results = self.collection.get(include=["metadatas"])
            if results and results["metadatas"]:
                for meta in results["metadatas"]:
                    if meta and "source_file" in meta:
                        self.indexed_files.add(meta["source_file"])

    # ------------------------------------------------------------------
    # CHUNKING
    # ------------------------------------------------------------------
    @staticmethod
    def _chunk_text(text, source_file):
        """
        Split a text into overlapping chunks.

        Why overlapping?
        If a sentence is cut at the boundary, the context is lost.
        Overlap ensures each chunk has some context from the previous one.

        Returns list of dicts: [{"text": "...", "source": "...", "index": 0}, ...]
        """
        # Normalize whitespace: collapse multiple newlines into one
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        chunks = []
        start = 0

        while start < len(text):
            # Find a good break point: try to end at a sentence or paragraph
            end = min(start + CHUNK_MAX_CHARS, len(text))

            if end < len(text):
                # Try to cut at a period + newline (paragraph boundary)
                paragraph_break = text.rfind(".\n", start, end)
                if paragraph_break > start + CHUNK_MIN_CHARS:
                    end = paragraph_break + 1  # include the period
                else:
                    # Try to cut at a period (sentence boundary)
                    sentence_break = text.rfind(". ", start, end)
                    if sentence_break > start + CHUNK_MIN_CHARS:
                        end = sentence_break + 1  # include the period
                    else:
                        # Try to cut at a newline
                        newline_break = text.rfind("\n", start, end)
                        if newline_break > start + CHUNK_MIN_CHARS:
                            end = newline_break

            chunk_text = text[start:end].strip()
            if chunk_text and len(chunk_text) >= CHUNK_MIN_CHARS / 2:
                chunks.append({
                    "text": chunk_text,
                    "source": source_file,
                    "index": len(chunks)
                })

            # Move forward, but leave some overlap
            start = end - CHUNK_OVERLAP if end < len(text) else len(text)

        return chunks

    @staticmethod
    def _get_file_hash(filepath):
        """
        Compute a quick hash of the file contents.
        Used to detect if a file has changed since last indexing.
        """
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    # ------------------------------------------------------------------
    # INDEXING
    # ------------------------------------------------------------------
    def build_index(self):
        """
        Read all .txt files from knowledge/, chunk them, embed them,
        and store in ChromaDB.

        Only re-indexes files that have changed (by content hash).
        """
        txt_files = sorted(KNOWLEDGE_DIR.glob("**/*.txt"))

        if not txt_files:
            print("[RAG] No .txt files found in knowledge/ or its subdirectories.")
            return

        print(f"[RAG] Found {len(txt_files)} knowledge file(s). Checking for changes...")

        all_chunks = []
        new_files = []

        for filepath in txt_files:
            current_hash = self._get_file_hash(filepath)
            # Store hash as a metadata marker — if the file content changes,
            # the hash changes, and we'll re-index it.
            file_key = f"{filepath.name}:{current_hash}"

            if file_key in self.indexed_files:
                print(f"[RAG]   Skipping (unchanged): {filepath.name}")
                continue

            print(f"[RAG]   Indexing: {filepath.name}")
            text = filepath.read_text(encoding="utf-8")
            chunks = self._chunk_text(text, filepath.name)
            all_chunks.extend(chunks)
            new_files.append(file_key)

        if not all_chunks:
            print("[RAG] All files are up to date. Nothing to index.")
            return

        print(f"[RAG] Embedding {len(all_chunks)} new chunk(s)...")

        # Step 2: Convert all chunks to vectors in one batch
        texts = [c["text"] for c in all_chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=True)

        # Step 3: Store in ChromaDB
        ids = []
        metadatas = []
        for i, chunk in enumerate(all_chunks):
            # ChromaDB needs unique IDs
            chunk_id = f"{chunk['source']}_chunk_{chunk['index']}"
            ids.append(chunk_id)
            metadatas.append({
                "source_file": f"{chunk['source']}:{self._get_file_hash(KNOWLEDGE_DIR / chunk['source'])}",
                "chunk_index": chunk["index"],
                "text": chunk["text"]
            })

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=[c["text"] for c in all_chunks],
            metadatas=metadatas,
            ids=ids
        )

        print(f"[RAG] Indexing complete. Collection now has {self.collection.count()} chunks.")

    # ------------------------------------------------------------------
    # RETRIEVAL
    # ------------------------------------------------------------------
    def retrieve(self, query, top_k=RETRIEVE_TOP_K):
        """
        Given a query string (e.g. the user's resume), find the top_k most
        similar chunks from the knowledge base.

        Steps:
        1. Embed the query into a vector
        2. Ask ChromaDB: "find the top_k vectors closest to this one"
        3. Return the text of those chunks

        Parameters:
            query (str): The text to search with (usually the user's resume)
            top_k (int): Number of chunks to return (default: 3)

        Returns:
            str: Concatenated text of the top_k most relevant chunks,
                 or an empty string if no chunks found.
        """
        if self.collection.count() == 0:
            print("[RAG] Empty collection. Call build_index() first or add knowledge files.")
            return ""

        print(f"[RAG] Retrieving top {top_k} chunks for query ({len(query)} chars)...")

        # Step 4: Embed the query
        query_embedding = self.embedder.encode([query])

        # Step 5: Search ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
        )

        if not results or not results["documents"] or not results["documents"][0]:
            print("[RAG] No relevant chunks found.")
            return ""

        # Step 6: Combine retrieved chunks into a single string
        retrieved_texts = results["documents"][0]
        distances = results["distances"][0] if results["distances"] else []

        print(f"[RAG] Retrieved {len(retrieved_texts)} chunk(s):")
        for i, (text, dist) in enumerate(zip(retrieved_texts, distances)):
            # Cosine similarity is 1 - distance/2 in ChromaDB's default metric
            # Lower distance = more similar
            preview = text[:80].replace("\n", " ")
            print(f"  [{i+1}] (distance: {dist:.4f}) {preview}...")

        return "\n\n".join(retrieved_texts)


# ---------------------------------------------------------------------------
# Convenience: get a pre-configured engine
# ---------------------------------------------------------------------------
_engine = None


def get_engine():
    """Get or create the singleton RAG engine."""
    global _engine
    if _engine is None:
        _engine = RagEngine()
    return _engine