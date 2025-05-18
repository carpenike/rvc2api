"""
RV-C specification JSON validation tool.

This script validates RV-C specification JSON data against a FAISS index of the RV-C document.
It helps ensure the JSON data aligns with the official specification by comparing DGN entries
with vector embeddings of the specification text.
"""

import json
import os
from pathlib import Path
from typing import Any

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Configuration constants
FAISS_INDEX_PATH: str = "resources/faiss/rvc_spec_f49bfc39f2db"
RVC_JSON_PATH: str = "rvc.json"
MODEL_NAME: str = "text-embedding-3-large"


def main() -> None:
    """
    Validate RV-C JSON data against the FAISS index of the specification.

    Loads and processes each DGN entry from the RV-C JSON file,
    queries the FAISS index for relevant specification content,
    and prints matching documentation for validation.

    Raises:
        FileNotFoundError: If either the FAISS index or RVC JSON file doesn't exist
        ValueError: If the JSON file is invalid or has an unexpected format
    """
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set")
    os.environ["OPENAI_API_KEY"] = api_key

    # Validate paths exist
    if not Path(FAISS_INDEX_PATH).exists():
        raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")
    if not Path(RVC_JSON_PATH).exists():
        raise FileNotFoundError(f"RV-C JSON file not found at {RVC_JSON_PATH}")

    # Load FAISS index
    vectorstore = FAISS.load_local(FAISS_INDEX_PATH, OpenAIEmbeddings(model=MODEL_NAME))

    # Load RV-C JSON data
    try:
        with open(RVC_JSON_PATH) as f:
            rvc_data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {RVC_JSON_PATH}: {e!s}") from e

    # Process each DGN in the RV-C JSON data
    for dgn_id, data in rvc_data.items():
        dgn_name = data.get("name", "")
        query = f"DGN {dgn_id} {dgn_name}"
        results = vectorstore.similarity_search(query, k=1)

        print(f"--- DGN {dgn_id} ({dgn_name}) ---")
        if results:
            context = results[0].page_content
            print(context[:1000])
        else:
            print("No matching documentation found.")
        print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
