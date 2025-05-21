#!/usr/bin/env python3
"""Test script for document_loader.py module."""

import json
from pathlib import Path

from document_loader import (
    ChunkingStrategy,
    filter_results_by_source,
    load_chunk_with_metadata,
)

# Test data
TEST_DATA_PATH = Path("resources/sample_chunks.json")


def main():
    """Run basic tests on document_loader functions."""
    print("Testing document_loader.py functionality...")

    # Load test data
    with open(TEST_DATA_PATH) as f:
        chunks_data = json.load(f)

    print(f"Loaded {len(chunks_data)} test chunks")

    # Test load_chunk_with_metadata
    docs = load_chunk_with_metadata(
        chunks_data=chunks_data,
        source_path=Path("test-document.pdf"),
        chunking_strategy=ChunkingStrategy.SECTION_OVERLAP,
    )

    print(f"Created {len(docs)} Document objects")

    # Print document content
    for doc in docs:
        print("\nDocument content:")
        print(f"Text: {doc.page_content}")
        print("Metadata:")
        for key, value in doc.metadata.items():
            print(f"  {key}: {value}")

    # Test filter_results_by_source
    filtered = filter_results_by_source(results=docs, source="test-document.pdf", limit=5)

    print(f"\nFiltered results count: {len(filtered)}")


if __name__ == "__main__":
    main()
