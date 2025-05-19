"""
Document loader utility for mixed sources in FAISS index.

This module provides utilities for loading and chunking documents from multiple sources
with different chunking strategies, ensuring consistent metadata for each chunk.
It supports the RV-C specification, Victron manuals, and other PDF sources.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from langchain.docstore.document import Document


class ChunkingStrategy(str, Enum):
    """Enumeration of supported chunking strategies."""

    SECTION_OVERLAP = "section_overlap"  # RV-C spec with section-based overlap
    PARAGRAPH = "paragraph"  # Standard paragraph chunking
    TOKEN = "token"  # Token-based chunking with fixed size
    SLIDING_WINDOW = "sliding_window"  # Sliding window with overlap


def normalize_source_name(path: Path) -> str:
    """
    Normalize the source name for consistent metadata.

    Args:
        path: Path to the source document

    Returns:
        A normalized source name suitable for metadata
    """
    # Special case for RV-C spec with various possible filenames
    name = path.name.lower()
    if "rv-c" in name or ("rvc" in name and "spec" in name):
        return "rvc-spec-2023-11.pdf"  # Standardized name

    # For other files, use the original name
    return path.name


def load_chunk_with_metadata(
    chunks_data: list[dict[str, Any]],
    source_path: Path,
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SECTION_OVERLAP,
) -> list[Document]:
    """
    Load chunks with consistent metadata for FAISS indexing.

    Args:
        chunks_data: List of chunk dictionaries with text content
        source_path: Path to the source document
        chunking_strategy: Chunking strategy used for this document

    Returns:
        List of Document objects with consistent metadata

    Raises:
        ValueError: If chunks_data contains invalid entries
    """
    docs = []
    source_name = normalize_source_name(source_path)

    for chunk in chunks_data:
        if "text" not in chunk:
            continue  # Skip chunks without text content

        # Build consistent metadata
        metadata = {
            # Extract standard fields
            "section": chunk.get("section", ""),
            "title": chunk.get("title", ""),
            "pages": chunk.get("pages", []),
            # Add source tracking
            "source": source_name,
            "chunking": chunking_strategy,
            # Preserve any other metadata
            **{k: v for k, v in chunk.items() if k not in ["text", "section", "title", "pages"]},
        }

        docs.append(Document(page_content=chunk["text"], metadata=metadata))

    return docs


def filter_results_by_source(
    results: list[Document],
    source: str | None = None,
    chunking: str | None = None,
    limit: int = 3,
) -> list[Document]:
    """
    Filter search results by source and chunking strategy.

    Args:
        results: List of document search results
        source: Optional source name to filter by
        chunking: Optional chunking strategy to filter by
        limit: Maximum number of results to return

    Returns:
        Filtered list of Document objects
    """
    if not (source or chunking):
        return results[:limit]

    filtered = []
    for doc in results:
        source_match = not source or doc.metadata.get("source") == source
        chunking_match = not chunking or doc.metadata.get("chunking") == chunking
        if source_match and chunking_match:
            filtered.append(doc)

    return filtered[:limit] if filtered else results[:limit]
