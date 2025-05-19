"""
RV-C specification search tool using FAISS vector database.

This script provides a command-line tool for querying the RV-C specification
using vector embeddings and semantic similarity search. It enables looking up
relevant specification sections based on natural language queries.
"""

import argparse
import os
from pathlib import Path

from document_loader import filter_results_by_source
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Configuration constants
FAISS_INDEX_PATH: str = (
    "resources/vector_store/rvc_spec_index"  # Updated path to match vector_service.py
)
MODEL_NAME: str = "text-embedding-3-large"
DEFAULT_RESULTS_COUNT: int = 3


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
    parser = argparse.ArgumentParser(description="Search RV-C specification with semantic search")
    parser.add_argument("query", nargs="+", help="The search query text")
    parser.add_argument("--source", "-s", help="Filter results by document source")
    parser.add_argument("--chunking", "-c", help="Filter results by chunking strategy")
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=DEFAULT_RESULTS_COUNT,
        help=f"Number of results to return (default: {DEFAULT_RESULTS_COUNT})",
    )

    args = parser.parse_args()
    query = " ".join(args.query).strip()

    if not query:
        parser.print_help()
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
    results = vectorstore.similarity_search(
        query, k=args.count + 5
    )  # Get extra results for filtering

    # Apply source/chunking filters using the helper function
    results = filter_results_by_source(
        results=results, source=args.source, chunking=args.chunking, limit=args.count
    )

    # Display results
    if not results:
        print(f"No results found for query: '{query}'")
        if args.source:
            print(f"Filter by source: {args.source}")
        if args.chunking:
            print(f"Filter by chunking strategy: {args.chunking}")
        return

    for i, doc in enumerate(results):
        print(f"--- Match {i + 1} ---")
        print(f"Source: {doc.metadata.get('source', 'unknown')}")
        print(f"Chunk strategy: {doc.metadata.get('chunking', 'unknown')}")
        print(f"Section: {doc.metadata.get('section', '')} - {doc.metadata.get('title', '')}")
        print(f"Pages: {doc.metadata.get('pages', [])}")
        print(doc.page_content[:1000])
        print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
