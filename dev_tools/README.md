# Developer Tools for RVC2API

This directory contains various developer tools and utility scripts for the RVC2API project. These tools are primarily designed for development, testing, and data processing tasks.

## RV-C Documentation Search Tools

This set of tools enables semantic searching of the RV-C specification documentation using vector embeddings and the FAISS library.

### `generate_embeddings.py`

Processes the RV-C specification PDF, extracts content by sections, and generates overlapping text chunks for better semantic search results.

**Usage:**

```bash
python generate_embeddings.py
```

**Configuration:**

- PDF_PATH: Path to the RV-C specification PDF (default: `resources/rv-c-spec.pdf`)
- OUTPUT_PATH: Path where the chunked JSON output will be saved (default: `resources/rvc_spec_chunks_with_overlap.json`)
- OVERLAP_LINES: Number of lines to overlap between chunks for better context

### `generate_faiss_index.py`

Converts the pre-processed text chunks into a FAISS vector index for efficient semantic searching.

**Usage:**

```bash
python generate_faiss_index.py
```

**Dependencies:**

- Requires OpenAI API key: `export OPENAI_API_KEY=your-api-key`
- Requires chunks file from `generate_embeddings.py`

**Configuration:**

- CHUNKS_PATH: Path to the JSON chunks file (default: `resources/rvc_spec_chunks_with_overlap.json`)
- FAISS_INDEX_PATH: Path where the FAISS index will be saved (default: `resources/vector_store/rvc_spec_index`)
- MODEL_NAME: OpenAI embedding model to use (default: `text-embedding-3-large`)

### `query_faiss.py`

Command-line tool for querying the RV-C specification using vector embeddings and semantic search.

**Usage:**

```bash
python query_faiss.py "your search query here"
```

**Dependencies:**

- Requires OpenAI API key: `export OPENAI_API_KEY=your-api-key`
- Requires generated FAISS index from `generate_faiss_index.py`

## Helper Script

A helper script is available in the `scripts` directory to simplify the setup process:

```bash
python scripts/setup_faiss.py --setup
```

This will guide you through the complete setup process for the RV-C documentation search functionality.

### `query_faiss.py`

Command-line tool for querying the RV-C specification using semantic search.

**Usage:**

```bash
python query_faiss.py "your search query here"
```

**Configuration:**

- FAISS_INDEX_PATH: Path to the FAISS index directory
- MODEL_NAME: OpenAI embeddings model to use (default: "text-embedding-3-large")

### `validate_rvc_json.py`

Validates RV-C specification JSON data against the FAISS index to ensure alignment with the official specification.

**Usage:**

```bash
python validate_rvc_json.py
```

**Configuration:**

- FAISS_INDEX_PATH: Path to the FAISS index directory
- RVC_JSON_PATH: Path to the RV-C JSON file to validate
- MODEL_NAME: OpenAI embeddings model to use (default: "text-embedding-3-large")

## Requirements

The scripts in this directory require:

1. Python 3.9+ with proper type annotations
2. OpenAI API key (set as OPENAI_API_KEY environment variable)
3. Additional Python packages (all included in the poetry devtools group):
   - langchain
   - langchain-openai
   - faiss-cpu or faiss-gpu
   - pymupdf (for PDF processing)

### Installing Dependencies

These dependencies are included in the project's development environment:

```bash
# Using Nix development shell
nix develop

# Or using Poetry directly
poetry install --with devtools
```

## Development Standards

All scripts in this directory follow the project's coding standards:

- Full type annotations with Python 3.9+ style (e.g., `list[dict[str, Any]]`)
- Comprehensive docstrings using Google style
- Proper error handling with descriptive error messages
- Consistent code organization and import ordering (stdlib → third-party → local)
