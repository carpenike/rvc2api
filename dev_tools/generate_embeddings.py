"""
RV-C specification PDF processor for FAISS embeddings.

This script processes a PDF of the RV-C specification, extracts text content by sections,
and generates overlapping chunks for better semantic search results. The resulting
chunks are saved as JSON for further processing with embeddings generation.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

# Configuration constants
PDF_PATH = Path("resources/rv-c-spec.pdf")  # Local path in project resources directory
OUTPUT_PATH = Path("resources/rvc_spec_chunks_with_overlap.json")  # Output to resources
OVERLAP_LINES = 5  # Number of overlapping lines between chunks


def chunk_pdf_with_overlap(pdf_path: Path, overlap: int = 5) -> list[dict[str, Any]]:
    """
    Process PDF into chunks with overlapping lines between sections.

    Args:
        pdf_path: Path to the PDF file to process
        overlap: Number of lines to overlap between chunks

    Returns:
        List of dictionaries containing chunked text with metadata

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
    """
    # Validate PDF exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Open PDF and prepare for processing
    doc = fitz.open(pdf_path)
    section_pattern = re.compile(r"^(\d+\.\d+(\.\d+)?)(\s+)(.+)")

    chunks = []
    current_chunk = []
    current_meta = {}
    previous_tail = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.splitlines()
        for line in lines:
            match = section_pattern.match(line.strip())
            if match:
                if current_chunk:
                    # Append previous tail for overlap
                    if previous_tail:
                        current_chunk = previous_tail + current_chunk
                    chunks.append(
                        {
                            "text": "\n".join(current_chunk).strip(),
                            "section": current_meta.get("section"),
                            "title": current_meta.get("title"),
                            "pages": list(set(current_meta.get("pages", []))),
                        }
                    )
                    # Save tail of current chunk for next overlap
                    previous_tail = (
                        current_chunk[-overlap:] if len(current_chunk) >= overlap else current_chunk
                    )
                    current_chunk = []

                section = match.group(1)
                title = match.group(4)
                current_meta = {
                    "section": section,
                    "title": title,
                    "pages": [page_num + 1],
                }
                current_chunk.append(f"Section: {section} {title}")
            elif current_chunk:
                current_chunk.append(line.strip())
                current_meta["pages"].append(page_num + 1)

    if current_chunk:
        # Add last chunk
        if previous_tail:
            current_chunk = previous_tail + current_chunk
        chunks.append(
            {
                "text": "\n".join(current_chunk).strip(),
                "section": current_meta.get("section"),
                "title": current_meta.get("title"),
                "pages": list(set(current_meta.get("pages", []))),
            }
        )

    return chunks


def main() -> None:
    """
    Process the RV-C specification PDF and generate overlapping chunks.

    Extracts text from the PDF, segments it by sections, adds overlapping lines
    between chunks for better semantic search context, and saves the result as JSON.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        PermissionError: If the output directory is not writable
    """
    try:
        print(f"Processing PDF: {PDF_PATH}")
        overlapping_chunks = chunk_pdf_with_overlap(PDF_PATH, OVERLAP_LINES)
        print(f"Generated {len(overlapping_chunks)} chunks with {OVERLAP_LINES} lines overlap")

        # Create parent directory if it doesn't exist
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write chunks to JSON file
        with open(OUTPUT_PATH, "w") as f:
            json.dump(overlapping_chunks, f, indent=2)

        print(f"Saved chunks to: {OUTPUT_PATH}")
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
