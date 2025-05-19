#!/usr/bin/env python3
"""
Test the document_loader with sample chunks.
This script demonstrates the process described in the PDF Processing Guide.
"""

import json
import sys
from pathlib import Path

from document_loader import ChunkingStrategy, load_chunk_with_metadata

# Configuration constants
CHUNKS_PATH = Path("resources/sample_chunks.json")
SOURCE_NAME = "sample-rv-c-manual.pdf"


def main() -> None:
    """
    Process sample chunks with document_loader.
    """
    try:
        print(f"Loading sample chunks from {CHUNKS_PATH}")

        # Load chunks from JSON file
        with open(CHUNKS_PATH) as f:
            chunks_data = json.load(f)

        print(f"Loaded {len(chunks_data)} chunks")

        # Convert to documents with proper metadata using the document_loader
        docs = load_chunk_with_metadata(
            chunks_data=chunks_data,
            source_path=Path(SOURCE_NAME),
            chunking_strategy=ChunkingStrategy.SECTION_OVERLAP,
        )

        print(f"Created {len(docs)} Document objects")

        # Display document content and metadata
        for i, doc in enumerate(docs, 1):
            print(f"\nDocument {i}:")
            print(f"Content: {doc.page_content[:50]}...")
            print("Metadata:")
            for key, value in doc.metadata.items():
                print(f"  {key}: {value}")

        print("\nSuccess! The document_loader is working correctly with the sample data.")
        print(
            "To add these documents to a FAISS index, follow the steps in the PDF Processing Guide."
        )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
