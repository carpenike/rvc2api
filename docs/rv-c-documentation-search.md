# RV-C Documentation Search

This guide explains how to set up and use the RV-C documentation search functionality in the rvc2api project.

## Overview

The rvc2api project includes a semantic search feature that allows users to query RV-C specification documentation using natural language. This feature is powered by:

1. FAISS vector database for efficient similarity search
2. OpenAI embeddings for converting text to vectors
3. FastAPI endpoints for accessing the search functionality

## Setup Instructions

### 1. Prepare the RV-C Specification PDF

Place the RV-C specification PDF in the resources directory:

```bash
cp /path/to/your/rv-c-spec.pdf resources/rv-c-spec.pdf
```

### 2. Set up OpenAI API Key

The embedding generation requires an OpenAI API key. Set it in your environment:

```bash
# For bash/zsh shells:
export OPENAI_API_KEY="your-openai-api-key"

# For fish shell:
set -x OPENAI_API_KEY "your-openai-api-key"
```

You can obtain an API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 3. Using the Helper Script (Recommended)

The easiest way to set up the documentation search is to use our helper script:

```bash
# Check the current setup status
poetry run python scripts/setup_faiss.py

# Run the complete setup process
poetry run python scripts/setup_faiss.py --setup
```

### 4. Manual Setup (Alternative)

If you prefer to set up each component manually:

First, generate text chunks from the PDF:

```bash
poetry run python dev_tools/generate_embeddings.py
```

This will:

- Process the PDF into text chunks with metadata
- Save the chunks to `resources/rvc_spec_chunks_with_overlap.json`

Then, generate the FAISS vector index:

```bash
poetry run python dev_tools/generate_faiss_index.py
```

This will:

- Convert the text chunks to document objects
- Generate embeddings using the OpenAI API
- Create and save a FAISS index to `resources/vector_store/rvc_spec_index`

### 5. Start/Restart the Server

Start or restart the FastAPI server to load the new index:

```bash
poetry run python src/core_daemon/main.py
```

## Using the Documentation Search

### Via Web Interface

The easiest way to use the search is through the web interface:

1. Open the web UI in your browser (typically at [http://localhost:8000](http://localhost:8000) or [http://localhost:5173](http://localhost:5173) for development)
2. Navigate to the "Documentation" page from the navigation menu
3. Use the search box to enter your query

### Via API Endpoint

You can query the documentation search through the API endpoint:

```bash
curl "http://localhost:8000/api/docs/search?query=battery%20charging%20parameters&k=3"
```

Parameters:

- `query`: (Required) Your natural language search query
- `k`: (Optional, default=3) Number of results to return (1-10)

### Via Command Line Tool

For quick testing without starting the server, use the CLI tool:

```bash
poetry run python dev_tools/query_faiss.py "battery charging parameters"
```

## Troubleshooting

If you encounter issues with the documentation search:

### Common Issues

1. **Search Not Available Error**: This typically means either:
   - The FAISS index hasn't been created yet
   - The OpenAI API key is missing or invalid
   - The server can't find the vector store files

2. **Missing PDF**: If you're missing the RV-C specification PDF:
   - Check your RV manufacturer's resources
   - Contact RVIA for access to the specification

3. **OpenAI API Issues**:
   - Verify your API key is valid and has sufficient quota
   - Check your billing status on the OpenAI dashboard
   - Try using a different API key if available

### Diagnostic Steps

1. Run the status check to identify issues:

   ```bash
   poetry run python scripts/setup_faiss.py --check
   ```

2. Verify file paths:
   - PDF: `resources/rv-c-spec.pdf`
   - Chunks file: `resources/rvc_spec_chunks_with_overlap.json`
   - FAISS index: `resources/vector_store/rvc_spec_index/`

3. Check server logs for specific error messages:

   ```bash
   # On most systems
   journalctl -u rvc2api.service -f

   # When running manually, check the terminal output
   ```

4. Test the search endpoint directly:

   ```bash
   curl -v "http://localhost:8000/api/docs/search?query=test"
   ```

### Advanced Troubleshooting

If the above steps don't resolve your issue:

1. Regenerate the chunks and index:

   ```bash
   rm resources/rvc_spec_chunks_with_overlap.json
   rm -rf resources/vector_store/rvc_spec_index
   poetry run python scripts/setup_faiss.py --setup
   ```

2. Check for Python package issues:

   ```bash
   poetry install
   ```

3. Verify the HTTP status from the API endpoint (503 means service unavailable)

For more detailed help, see the project documentation or create an issue on GitHub.
