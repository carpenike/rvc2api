# Developer Tools for RVC2API

This directory contains various developer tools and utility scripts for the RVC2API project. These tools are primarily designed for development, testing, and data processing tasks.

## RV-C Documentation Search Tools

This set of tools enables semantic searching of RV-C and other technical documentation using vector embeddings and the FAISS library. The system supports mixed chunking strategies in a single FAISS index, allowing efficient search across multiple document types with different formats.

For detailed instructions on the enhanced mixed chunking capabilities, see [the PDF Processing Guide](../docs/pdf-processing-guide.md).

### `enhanced_document_processor.py`

A versatile PDF processor that supports multiple chunking strategies and auto-detection of optimal strategies based on document structure. This is the recommended tool for processing PDFs for vector search.

**Key Features:**

- Multiple chunking strategies (section-based, paragraph-based, sliding window, token-based)
- Auto-detection of optimal chunking strategy
- Direct FAISS index integration
- Source tag customization
- Comprehensive processing summary
- Dry run mode for testing
- Enhanced error handling

**Usage:**

```bash
# Basic usage with auto-detection
poetry run python enhanced_document_processor.py --pdf resources/your-document-name.pdf

# Process and add directly to FAISS index
poetry run python enhanced_document_processor.py --pdf resources/your-document-name.pdf --add-to-index resources/vector_store/index

# Override source tag in metadata
poetry run python enhanced_document_processor.py --pdf resources/your-document-name.pdf --source-tag "standard-name.pdf"

# Test without saving files
poetry run python enhanced_document_processor.py --pdf resources/your-document-name.pdf --dry-run
```

For complete documentation, run `poetry run python enhanced_document_processor.py --help`

### `generate_embeddings.py` (Legacy)

Processes the RV-C specification PDF, extracts content by sections, and generates overlapping text chunks for better semantic search results.

**Usage:**

```bash
python generate_embeddings.py
```

**Configuration:**

- PDF_PATH: Path to the RV-C specification PDF (default: `resources/rvc-spec-2023-11.pdf`)
- OUTPUT_PATH: Path where the chunked JSON output will be saved (default: `resources/rvc_spec_chunks_with_overlap.json`)
- OVERLAP_LINES: Number of lines to overlap between chunks for better context
- CHUNKING_STRATEGY: Identifier for the chunking method used (default: `section_overlap`)

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

Command-line tool for querying the RV-C specification using vector embeddings and semantic search. Supports filtering by document source and chunking strategy.

**Usage:**

```bash
# Basic search
python query_faiss.py "your search query here"

# Filter by document source
python query_faiss.py "your search query here" --source rvc-spec-2023-11.pdf

# Filter by chunking strategy
python query_faiss.py "your search query here" --chunking section_overlap

# Control number of results
python query_faiss.py "your search query here" --count 5
```

**Dependencies:**

- Requires OpenAI API key: `export OPENAI_API_KEY=your-api-key`
- Requires generated FAISS index from `generate_faiss_index.py`

**Configuration:**

- FAISS_INDEX_PATH: Path to the FAISS index (default: `resources/vector_store/rvc_spec_index`)
- MODEL_NAME: OpenAI embedding model to use (default: `text-embedding-3-large`)
- DEFAULT_RESULTS_COUNT: Number of results to return when not specified (default: `3`)

## Enhanced Document Loader

The tool suite now includes a document loader module that supports mixed chunking strategies:

### `document_loader.py`

Utility module for loading multiple document sources with different chunking strategies into a unified FAISS index.

**Features:**

- Supports multiple document sources in a single FAISS index
- Maintains consistent metadata across document types
- Provides unified filtering by source and chunking strategy
- Normalizes source names for consistent identification

**Available chunking strategies:**

- `section_overlap`: Section-based chunking with overlap (ideal for specifications like RV-C)
- `paragraph`: Paragraph-based chunking (good for manuals and guides)
- `token`: Fixed token-size chunks (consistent size for embedding)
- `sliding_window`: Sliding window chunking with overlap

### `validate_rvc_json.py`

Validates RV-C specification JSON data against the FAISS index to ensure alignment with the official documentation.

**Usage:**

```bash
python validate_rvc_json.py
```

**Configuration:**

- FAISS_INDEX_PATH: Path to the FAISS index directory
- RVC_JSON_PATH: Path to the RV-C JSON file to validate
- MODEL_NAME: OpenAI embeddings model to use (default: "text-embedding-3-large")
- DEFAULT_SOURCE: Preferred source document for validation (default: "rvc-spec-2023-11.pdf")

## Requirements

The scripts in this directory require:

1. Python 3.9+ with proper type annotations
2. OpenAI API key (set as OPENAI_API_KEY environment variable)
3. LangChain libraries for document processing
4. FAISS vector database for embedding storage and retrieval

## Multi-Source Document Search

This tool suite now supports multiple document sources in a single FAISS index:

1. **RV-C Specification**: Section-based chunking with overlap
2. **Victron Manuals**: Can be added using paragraph-based chunking
3. **Other Equipment Manuals**: Can be added with appropriate chunking strategies

Each document source maintains its own metadata for tracking purposes, allowing you to:

- Filter search results by document source
- Apply different chunking strategies for different document types
- Maintain a unified search interface across all documentation

### Example: Mixing Document Sources

```python
from document_loader import ChunkingStrategy, load_chunk_with_metadata

# Load RV-C spec chunks with section-based overlap
rvc_chunks = load_chunk_with_metadata(
    chunks_data=rvc_spec_chunks,
    source_path=Path("resources/rvc-spec-2023-11.pdf"),
    chunking_strategy=ChunkingStrategy.SECTION_OVERLAP
)

# Load Victron manual with paragraph chunking
victron_chunks = load_chunk_with_metadata(
    chunks_data=victron_chunks,
    source_path=Path("resources/victron-multiplus-manual.pdf"),
    chunking_strategy=ChunkingStrategy.PARAGRAPH
)

# Combine all documents in one index
all_docs = rvc_chunks + victron_chunks
vectorstore = FAISS.from_documents(all_docs, embeddings)
```

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
