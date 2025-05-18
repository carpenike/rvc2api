#!/usr/bin/env python3
"""
Generate FAISS index from RV-C specification JSON chunks.

This script takes the preprocessed JSON chunks from the RV-C specification
and creates a FAISS vector index for semantic searching.
"""

import json
import os
import sys
from pathlib import Path

from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Configuration constants
CHUNKS_PATH = Path("resources/rvc_spec_chunks_with_overlap.json")
FAISS_INDEX_PATH = Path("resources/vector_store/rvc_spec_index")
MODEL_NAME = "text-embedding-3-large"


def main() -> None:
    """
    Generate a FAISS index from preprocessed RV-C specification JSON chunks.

    Reads the JSON file with text chunks, converts them to Document objects,
    generates embeddings, and saves the resulting FAISS index.

    Raises:
        FileNotFoundError: If the JSON file with chunks doesn't exist
        ValueError: If the JSON file doesn't contain proper data
    """
    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Validate chunks file
    if not CHUNKS_PATH.exists():
        print(f"Error: Chunks file not found at {CHUNKS_PATH}")
        print("Run generate_embeddings.py first to create the chunks file.")
        sys.exit(1)

    # Load chunks
    try:
        with open(CHUNKS_PATH) as f:
            chunks_data = json.load(f)

        print(f"Loaded {len(chunks_data)} chunks from {CHUNKS_PATH}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading chunks file: {e}")
        sys.exit(1)

    # Convert to documents
    docs = []
    for chunk in chunks_data:
        if "text" not in chunk:
            print("Warning: Chunk missing 'text' field, skipping")
            continue

        metadata = {
            "section": chunk.get("section", ""),
            "title": chunk.get("title", ""),
            "pages": chunk.get("pages", []),
        }

        docs.append(Document(page_content=chunk["text"], metadata=metadata))

    print(f"Created {len(docs)} Document objects")

    # Create embeddings and FAISS index
    try:
        print(f"Generating embeddings using OpenAI model: {MODEL_NAME}")
        embeddings = OpenAIEmbeddings(model=MODEL_NAME)

        print("Creating FAISS index...")
        vectorstore = FAISS.from_documents(docs, embeddings)

        # Ensure the directory exists
        FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Save the index
        print(f"Saving FAISS index to {FAISS_INDEX_PATH}")
        vectorstore.save_local(FAISS_INDEX_PATH)

        print(f"Successfully created and saved FAISS index to {FAISS_INDEX_PATH}")
        print("\nYou can now search the index with:")
        print("  python dev_tools/query_faiss.py 'your search query'")

    except Exception as e:
        print(f"Error creating embeddings or FAISS index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
