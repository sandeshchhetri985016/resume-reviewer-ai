"""
rag_demo.py — Terminal demo for the RAG engine.

This script demonstrates the RAG pipeline WITHOUT the Streamlit UI.
Run it to see exactly how chunking, embedding, and retrieval work.

Usage:
    python rag_demo.py

What it does:
    1. Builds/updates the vector index from knowledge/*.txt
    2. Lets you type queries and see which chunks are retrieved
    3. Shows distance scores so you can judge relevance

Type 'quit' to exit.
"""

from rag_engine import get_engine


def main():
    print("=" * 70)
    print("  RAG Engine Demo")
    print("=" * 70)
    print()
    print("Step 1: Initialize the RAG engine...")
    print("  (This will download the embedding model ~80 MB on first run)")
    print()

    engine = get_engine()

    print()
    print("Step 2: Build/update the index from knowledge/*.txt ...")
    print()
    engine.build_index()

    print()
    print("=" * 70)
    print("  Ready! Type a query (or 'quit' to exit)")
    print("  Example queries:")
    print('    - "aged care resume tips"')
    print('    - "NDIS keywords"')
    print('    - "action verbs for support worker"')
    print("=" * 70)
    print()

    while True:
        query = input("🔍 Query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not query:
            continue

        print()
        result = engine.retrieve(query, top_k=3)
        print()

        if result:
            print("─" * 70)
            print("  RETRIEVED CHUNKS:")
            print("─" * 70)
            print(result)
            print("─" * 70)
        else:
            print("  No relevant chunks found.")

        print()


if __name__ == "__main__":
    main()