"""
rag_engine.py — RAG (Retrieval-Augmented Generation) for Resume Reviewer

What this does:
1. Reads all .txt files from the knowledge/ directory
2. Splits them into overlapping chunks (200-500 chars)
3. Converts each chunk into a vector embedding (384 numbers)
4. Stores vectors in a local ChromaDB database
5. At query time, classifies resume domain, then finds most similar chunks within that domain
"""

import os
import re
import hashlib
import warnings
import tarfile
import shutil
from datetime import datetime
from pathlib import Path

# Suppress noisy transformers submodule path warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*Accessing `__path__`.*")
warnings.filterwarnings("ignore", message=".*Examining the path of.*")

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

# ---------------------------------------------------------------------------
# Domain descriptions for embedding-based classification
# Each description captures what a typical resume in that domain looks like.
# The embedder (already loaded) converts these to vectors, then we compare
# the resume embedding against each domain embedding via cosine similarity.
# This is far more accurate than keyword counting and costs nothing extra
# since the embedder is already loaded for RAG.
# ---------------------------------------------------------------------------
DOMAIN_DESCRIPTIONS = {
    "healthcare": (
        "Personal care worker support worker disability support aged care ndis patient care "
        "medication assistance manual handling dementia palliative care daily living support "
        "community access client advocacy care plans"
    ),
    "nursing": (
        "Registered nurse enrolled nurse ahpra medication administration wound care "
        "vital signs patient assessment clinical handover triage iv therapy "
        "nursing care plans clinical documentation infection control"
    ),
    "aged_care": (
        "Aged care residential aged care nursing home dementia care acfi an-acc "
        "falls prevention pressure care continence mealtime management "
        "home care packages chsp personal care elderly support"
    ),
    "software_engineering": (
        "Software engineer developer python java javascript react node django "
        "full stack backend frontend api microservices aws docker kubernetes "
        "git ci cd agile scrum sql database system design testing"
    ),
    "cloud_engineering": (
        "Cloud engineer devops aws azure gcp terraform kubernetes docker "
        "infrastructure as code cloud migration ci cd pipelines monitoring "
        "site reliability high availability disaster recovery security"
    ),
    "data_science": (
        "Data scientist data analyst machine learning deep learning python "
        "sql statistics tensorflow pytorch a b testing data visualization "
        "tableau power bi predictive modeling feature engineering"
    ),
    "cyber_security": (
        "Cyber security information security penetration testing ethical hacking "
        "cissp firewall siem vulnerability assessment incident response "
        "risk assessment compliance nist iso 27001 threat intelligence"
    ),
    "accounting": (
        "Accountant accounting cpa ca bookkeeping financial reporting "
        "xero quickbooks myob sap reconciliation budgeting forecasting "
        "tax gst bas audit month end close balance sheet"
    ),
    "marketing": (
        "Marketing digital marketing seo sem google ads social media "
        "content marketing email marketing hubspot google analytics "
        "campaign conversion lead generation brand roi roas"
    ),
    "hr": (
        "Human resources hr recruitment talent acquisition employee relations "
        "payroll performance management onboarding training workday "
        "industrial relations fair work policy development whs"
    ),
    "logistics": (
        "Logistics supply chain warehouse inventory management freight "
        "distribution transport fleet procurement shipping receiving "
        "wms sap on time delivery demand planning continuous improvement"
    ),
    "construction": (
        "Construction trade builder carpenter bricklayer stonemason roofer "
        "excavator bulldozer crane operator rigger concreter formwork "
        "structural steel welding fabrication demolition earthmoving"
    ),
    "electrician": (
        "Electrician electrical a grade switchboard wiring cabling "
        "solar pv test and tag fault finding motor control "
        "commercial industrial domestic fire panel data cabling"
    ),
    "plumber": (
        "Plumber plumbing gas fitter gas fitting drainage hot water "
        "sewer stormwater roofing pipe backflow water supply "
        "commercial domestic maintenance excavation"
    ),
    "aviation": (
        "Pilot aviation flight casa atpl cpl ppl instrument rating "
        "multi engine type rating first officer crew resource management "
        "safety simulator check ride commercial operations"
    ),
    "mobile_development": (
        "Mobile developer ios android swift kotlin flutter react native "
        "app store google play uikit swiftui jetpack compose "
        "push notifications offline storage mobile architecture"
    ),
}


class RagEngine:
    """
    A minimal RAG engine with domain-aware retrieval.

    Usage:
        engine = RagEngine()
        engine.build_index()          # Run once to index all knowledge files
        chunks = engine.retrieve("resume for aged care")  # Get top 3 relevant chunks
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
        print("[RAG] Loading embedding model:", EMBEDDING_MODEL_NAME)
        self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("[RAG] Model loaded successfully.")

        # Step B: Connect to ChromaDB (creates ./chroma_db/ directory on first run)
        CHROMA_DB_DIR.mkdir(exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

        # Step C: Get or create the collection
        try:
            self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
            print(f"[RAG] Found existing collection '{COLLECTION_NAME}' "
                  f"with {self.collection.count()} chunks.")
        except (KeyError, ValueError):
            # Collection doesn't exist, create new one
            self.collection = self.chroma_client.create_collection(COLLECTION_NAME)
            print(f"[RAG] Created new collection '{COLLECTION_NAME}'.")

        # Step D: Track which files have been indexed (by content hash)
        self.indexed_files = set()
        if self.collection.count() > 0:
            results = self.collection.get(include=["metadatas"])
            if results and results["metadatas"]:
                for meta in results["metadatas"]:
                    if meta and "source_file" in meta:
                        self.indexed_files.add(meta["source_file"])

        # Step E: Domain embeddings cache (lazy-loaded on first classify)
        self._domain_embeddings = None
        self._domain_names = None

        # Step F: Backup and recovery on startup
        self._ensure_backup()

    def _ensure_backup(self):
        """Create a backup of ChromaDB on startup, keeping last 3 backups."""
        if not CHROMA_DB_DIR.exists():
            return
        
        backup_dir = CHROMA_DB_DIR.parent / "chroma_db_backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"chroma_db_backup_{timestamp}.tar.gz"
        
        try:
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(CHROMA_DB_DIR, arcname="chroma_db")
            print(f"[RAG] Backup created: {backup_path}")
        except Exception as backup_error:
            print(f"[RAG] Warning: Could not create backup: {backup_error}")
            return
        
        # Clean up old backups (keep only last 3)
        try:
            backups = sorted(backup_dir.glob("chroma_db_backup_*.tar.gz"))
            if len(backups) > 3:
                for old_backup in backups[:-3]:
                    old_backup.unlink()
                    print(f"[RAG] Removed old backup: {old_backup.name}")
        except Exception as cleanup_error:
            print(f"[RAG] Warning: Could not clean old backups: {cleanup_error}")

    @staticmethod
    def recover_from_backup():
        """Recover ChromaDB from the latest backup if main DB is corrupted."""
        backup_dir = CHROMA_DB_DIR.parent / "chroma_db_backups"
        if not backup_dir.exists():
            print("[RAG] No backups available for recovery.")
            return False
        
        backups = sorted(backup_dir.glob("chroma_db_backup_*.tar.gz"), reverse=True)
        if not backups:
            print("[RAG] No backups found.")
            return False
        
        latest_backup = backups[0]
        try:
            # Remove corrupted DB
            if CHROMA_DB_DIR.exists():
                import shutil
                shutil.rmtree(CHROMA_DB_DIR)
            
            # Extract backup
            with tarfile.open(latest_backup, "r:gz") as tar:
                tar.extractall(path=CHROMA_DB_DIR.parent)
            
            print(f"[RAG] Successfully recovered from backup: {latest_backup.name}")
            return True
        except Exception as recovery_error:
            print(f"[RAG] Recovery failed: {recovery_error}")
            return False

    @staticmethod
    def _domain_to_chunk_domain(domain: str) -> list:
        """
        Map classifier domain names to actual ChromaDB domain metadata values.
        The ChromaDB domain metadata is derived from the filename (e.g., 'healthcare_keywords.txt' → 'healthcare_keywords').
        The classifier returns canonical names (e.g., 'healthcare').
        This mapping ensures they match.
        """
        mapping = {
            "healthcare": ["healthcare_keywords"],
            "nursing": ["nursing"],
            "aged_care": ["aged_care"],
            "software_engineering": ["software_engineering"],
            "cloud_engineering": ["cloud_engineering"],
            "data_science": ["data_science"],
            "cyber_security": ["cyber_security"],
            "accounting": ["accounting"],
            "marketing": ["marketing"],
            "hr": ["hr"],
            "logistics": ["logistics"],
            "construction": ["construction"],
            "electrician": ["electrician"],
            "plumber": ["plumber"],
            "aviation": ["aviation"],
            "mobile_development": ["mobile_development"],
        }
        return mapping.get(domain, [domain])

    # ------------------------------------------------------------------
    # DOMAIN CLASSIFICATION — embedding-based, uses pre-loaded embedder
    # ------------------------------------------------------------------
    def classify_domain(self, text: str) -> tuple:
        """
        Classify text into a career domain using embedding similarity.
        Uses the already-loaded sentence-transformer model (zero extra cost).

        Returns:
            (best_domain: str, similarity: float, all_similarities: list)
            - best_domain: the most similar domain key
            - similarity: cosine similarity score (0-1, higher = more similar)
            - all_similarities: list of (domain, similarity) for all domains
        """
        if self._domain_embeddings is None:
            print("[RAG] Pre-computing domain embeddings for classification...")
            domain_texts = list(DOMAIN_DESCRIPTIONS.values())
            self._domain_embeddings = self.embedder.encode(domain_texts)
            self._domain_names = list(DOMAIN_DESCRIPTIONS.keys())
            print(f"[RAG] Computed {len(self._domain_embeddings)} domain embeddings.")

        # Embed the query text
        query_emb = self.embedder.encode([text])[0]

        # Compute cosine similarities against all domain embeddings
        similarities = []
        for i, domain_vec in enumerate(self._domain_embeddings):
            dot = sum(q * d for q, d in zip(query_emb, domain_vec))
            norm_q = sum(q * q for q in query_emb) ** 0.5
            norm_d = sum(d * d for d in domain_vec) ** 0.5
            sim = dot / (norm_q * norm_d) if norm_q * norm_d > 0 else 0
            similarities.append((self._domain_names[i], sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: -x[1])
        best = similarities[0]

        return (best[0], round(best[1], 4), similarities)

    # ------------------------------------------------------------------
    # CHUNKING
    # ------------------------------------------------------------------
    @staticmethod
    def _chunk_text(text, source_file):
        """
        Split a text into chunks with heading-aware boundaries.
        Each chunk starts at a heading boundary (## , ## Key, etc.) or paragraph break.
        This prevents mid-sentence fragments and keeps logical sections intact.
        """
        # Normalize whitespace
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        # Find all heading positions (lines starting with ##)
        # Also treat lines starting with section numbers (1., 2., etc.) as potential boundaries
        heading_positions = []
        for m in re.finditer(r"^##?\s+\w|^\d+\.\s+\w|^KEY|^RESUME|^COMMON|^CRITICAL|^CERTIFICATIONS|^METRICS|^RESUME STRUCTURE|^RED FLAGS", text, re.MULTILINE):
            heading_positions.append(m.start())

        chunks = []
        if not heading_positions:
            # No headings found — fall back to paragraph-based splitting
            heading_positions = [0]
            for m in re.finditer(r"\n\n", text):
                heading_positions.append(m.end())

        # Build chunks from heading boundaries
        for i, start in enumerate(heading_positions):
            if i + 1 < len(heading_positions):
                end = heading_positions[i + 1]
            else:
                end = len(text)

            chunk_text = text[start:end].strip()
            if not chunk_text:
                continue

            # If chunk is too large, split it at paragraph boundaries
            if len(chunk_text) > CHUNK_MAX_CHARS:
                # Find paragraph breaks within this chunk
                para_breaks = [m.end() for m in re.finditer(r"\n\n", chunk_text)]
                if para_breaks:
                    sub_start = 0
                    for pb in para_breaks:
                        sub_chunk = chunk_text[sub_start:pb].strip()
                        if sub_chunk:
                            chunks.append({
                                "text": sub_chunk,
                                "source": source_file,
                                "index": len(chunks)
                            })
                        sub_start = pb
                    # Remaining after last paragraph break
                    remaining = chunk_text[sub_start:].strip()
                    if remaining:
                        chunks.append({
                            "text": remaining,
                            "source": source_file,
                            "index": len(chunks)
                        })
                else:
                    # No paragraph breaks — split at sentence boundaries
                    sentences = re.split(r"(?<=\.) ", chunk_text)
                    sub_chunk = ""
                    for sent in sentences:
                        if len(sub_chunk) + len(sent) < CHUNK_MAX_CHARS:
                            sub_chunk += sent + " "
                        else:
                            if sub_chunk.strip():
                                chunks.append({
                                    "text": sub_chunk.strip(),
                                    "source": source_file,
                                    "index": len(chunks)
                                })
                            sub_chunk = sent + " "
                    if sub_chunk.strip():
                        chunks.append({
                            "text": sub_chunk.strip(),
                            "source": source_file,
                            "index": len(chunks)
                        })
            else:
                chunks.append({
                    "text": chunk_text,
                    "source": source_file,
                    "index": len(chunks)
                })

        return chunks

    @staticmethod
    def _get_file_hash(filepath):
        """Compute a quick hash of the file contents."""
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    # ------------------------------------------------------------------
    # INDEXING
    # ------------------------------------------------------------------
    def build_index(self):
        """
        Read all .txt files from knowledge/, chunk them, embed them,
        and store in ChromaDB. Only re-indexes changed files.
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

        texts = [c["text"] for c in all_chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=True)

        ids = []
        metadatas = []
        for i, chunk in enumerate(all_chunks):
            chunk_id = f"{chunk['source']}_chunk_{chunk['index']}"
            domain_key = chunk['source'].replace('.txt', '')
            ids.append(chunk_id)
            metadatas.append({
                "source_file": f"{chunk['source']}:{self._get_file_hash(KNOWLEDGE_DIR / chunk['source'])}",
                "chunk_index": chunk["index"],
                "text": chunk["text"],
                "domain": domain_key
            })

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=[c["text"] for c in all_chunks],
            metadatas=metadatas,
            ids=ids
        )

        print(f"[RAG] Indexing complete. Collection now has {self.collection.count()} chunks.")

    # ------------------------------------------------------------------
    # RETRIEVAL — with embedding-based domain classification + graceful fallback
    # ------------------------------------------------------------------
    def retrieve(self, query, top_k=RETRIEVE_TOP_K):
        """
        Given a resume text, find the top_k most relevant knowledge chunks.

        Uses embedding-based domain classification to narrow search to
        the most relevant domain(s), preventing cross-domain noise.

        Strategy:
        - High confidence (>0.6): search only the top domain
        - Medium confidence (0.4-0.6): search top 2 domains
        - Low confidence (<0.4): search all domains
        - Fallback on empty results: search all domains

        Returns:
            str: Concatenated text of the most relevant chunks
        """
        if self.collection.count() == 0:
            print("[RAG] Empty collection. Call build_index() first.")
            return ""

        print(f"[RAG] Retrieving top {top_k} chunks for query ({len(query)} chars)...")

        # Step 1: Classify domain using embedding similarity
        best_domain, sim, all_sims = self.classify_domain(query)
        print(f"[RAG] Best domain: {best_domain} (similarity: {sim})")

        # Log top 3 domains for debugging
        for d, s in all_sims[:3]:
            print(f"[RAG]   {d}: {s}")

        # Step 2: Determine which domains to search
        # Use margin-based confidence: if #1 and #2 are very close, search both
        # This handles ambiguous cases like healthcare vs aged_care (0.73 vs 0.72)
        domains_to_search = []
        second_domain = all_sims[1][0] if len(all_sims) > 1 else best_domain
        margin = sim - all_sims[1][1] if len(all_sims) > 1 else 1.0

        if margin < 0.03:
            # Very close margin — search top 2 regardless of raw score
            domains_to_search = [best_domain, second_domain]
            print(f"[RAG] Tight margin ({margin:.4f}) — searching both: {best_domain}, {second_domain}")
        elif sim >= 0.6:
            # High confidence with clear winner — search only top domain
            domains_to_search = [best_domain]
            print(f"[RAG] High confidence — searching domain: {best_domain}")
        elif sim >= 0.4:
            # Medium confidence — search top 2
            domains_to_search = [best_domain, second_domain]
            print(f"[RAG] Medium confidence — searching domains: {best_domain}, {second_domain}")
        else:
            # Low confidence — search all
            print(f"[RAG] Low confidence — searching all domains")
            domains_to_search = [d for d, _ in all_sims]

        # Step 3: Embed the query
        query_embedding = self.embedder.encode([query])

        # Step 4: Search ChromaDB with domain filter(s)
        retrieved_texts = []

        for domain in domains_to_search:
            # Map classifier domain to actual ChromaDB metadata values
            chunk_domains = self._domain_to_chunk_domain(domain)
            if not chunk_domains:
                continue
            # Use $in operator to match any of the mapped chunk domains
            domain_filter = {"domain": {"$in": chunk_domains}}
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k,
                where=domain_filter
            )

            if results and results["documents"] and results["documents"][0]:
                for doc in results["documents"][0]:
                    if doc not in retrieved_texts:
                        retrieved_texts.append(doc)

            if len(retrieved_texts) >= top_k:
                break

        # Step 5: Fallback — if no results, search all domains
        if not retrieved_texts:
            print("[RAG] No results from domain-filtered search. Falling back to full search.")
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k
            )
            if results and results["documents"] and results["documents"][0]:
                retrieved_texts = results["documents"][0]

        if not retrieved_texts:
            return ""

        # Limit to top_k
        retrieved_texts = retrieved_texts[:top_k]

        print(f"[RAG] Retrieved {len(retrieved_texts)} chunk(s):")
        for i, text in enumerate(retrieved_texts):
            preview = text[:80].replace("\n", " ")
            print(f"  [{i+1}] {preview}...")

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