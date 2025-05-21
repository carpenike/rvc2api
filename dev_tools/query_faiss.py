import argparse
import builtins
import os
from enum import Enum
from pathlib import Path

from document_loader import ChunkingStrategy, filter_results_by_source
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Embedding options
from langchain_openai import OpenAIEmbeddings

FAISS_INDEX_PATH: str = "resources/vector_store"
OPENAI_MODEL: str = "text-embedding-3-large"
HF_MODEL: str = "all-MiniLM-L6-v2"
DEFAULT_RESULTS_COUNT: int = 3


class ChunkingMethod(str, Enum):
    SECTION_OVERLAP = "section_overlap"
    PARAGRAPH = "paragraph"
    TOKEN = "token"
    SLIDING_WINDOW = "sliding_window"


# Trick to make pickle recognize it
builtins.ChunkingMethod = ChunkingMethod


def load_embeddings() -> object:
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")

    if api_key:
        try:
            print("✅ Using OpenAIEmbeddings")
            return OpenAIEmbeddings(
                model=OPENAI_MODEL,
                openai_api_base=api_base or None,
            )
        except Exception as e:
            print(f"⚠️ Failed to initialize OpenAIEmbeddings: {e}. Falling back to HuggingFace.")

    print("⚠️ OPENAI_API_KEY not set or failed. Using HuggingFaceEmbeddings")
    return HuggingFaceEmbeddings(model_name=HF_MODEL)


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic search against RV-C spec FAISS index")
    parser.add_argument("query", nargs="+", help="Natural language query")
    parser.add_argument("--source", "-s", help="Filter by document source")
    parser.add_argument("--chunking", "-c", choices=[c.value for c in ChunkingStrategy])
    parser.add_argument(
        "--count", "-n", type=int, default=DEFAULT_RESULTS_COUNT, help="Number of matches to show"
    )

    args = parser.parse_args()
    query = " ".join(args.query).strip()

    if not query:
        print("❌ Empty query. Please provide a search term.")
        return

    if not Path(FAISS_INDEX_PATH).exists():
        raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

    embeddings = load_embeddings()

    try:
        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(f"❌ Failed to load FAISS index: {e}")
        return

    results = vectorstore.similarity_search(query, k=args.count + 5)
    results = filter_results_by_source(results, args.source, args.chunking, limit=args.count)

    if not results:
        print("No results found.")
        return

    for i, doc in enumerate(results):
        print(f"\n--- Match {i + 1} ---")
        print(f"Source: {doc.metadata.get('source')}")
        print(f"Chunking: {doc.metadata.get('chunking')}")
        print(f"Section: {doc.metadata.get('section', '')} - {doc.metadata.get('title', '')}")
        print(f"Pages: {doc.metadata.get('pages')}")
        print("\n" + doc.page_content[:1000])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}")
