"""
RV-C specification search tool using FAISS vector database.

This script provides a command-line tool for querying the RV-C specification
using vector embeddings and semantic similarity search. It enables looking up
relevant specification sections based on natural language queries.
"""

import os
import sys
from pathlib import Path

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Configuration constants
FAISS_INDEX_PATH: str = (
    "resources/vector_store/rvc_spec_index"  # Updated path to match vector_service.py
)
MODEL_NAME: str = "text-embedding-3-large"


def main() -> None:
    """
    Query the FAISS index for RV-C specification content.

    Takes command line arguments as the search query, retrieves the most
    relevant sections from the RV-C specification, and displays them
    with their metadata.

    Raises:
        FileNotFoundError: If the FAISS index doesn't exist
    """
    # Process command line arguments
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print("Usage: python query_faiss.py <query string>")
        return

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set")
    os.environ["OPENAI_API_KEY"] = api_key

    # Validate FAISS index exists
    if not Path(FAISS_INDEX_PATH).exists():
        raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

    # Load FAISS index and perform search
    vectorstore = FAISS.load_local(FAISS_INDEX_PATH, OpenAIEmbeddings(model=MODEL_NAME))
    results = vectorstore.similarity_search(query, k=3)

    # Display results
    for i, doc in enumerate(results):
        print(f"--- Match {i + 1} ---")
        print(f"Section: {doc.metadata.get('section')} - {doc.metadata.get('title')}")
        print(f"Pages: {doc.metadata.get('pages')}")
        print(doc.page_content[:1000])
        print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
