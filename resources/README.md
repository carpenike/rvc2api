# Resources Directory

This directory contains non-code assets used by the rvc2api project, including:

## RV-C Specification

The RV-C specification PDF should be placed here as:
- `rv-c-spec.pdf`

This file is used by the `dev_tools/generate_embeddings.py` script to create text chunks and FAISS embeddings for semantic searching.

## Vector Store

The `vector_store/` directory contains FAISS indices generated from the RV-C specification. These files enable fast semantic search of the specification content.

- `vector_store/rvc_spec_index/` - FAISS index directory

## Usage

1. Place the RV-C specification PDF in this directory as `rv-c-spec.pdf`
2. Generate embeddings using the dev tool: `poetry run python dev_tools/generate_embeddings.py`
3. The generated chunks and FAISS index will be stored here

## Environment Variables

To use an OpenAI API key for embeddings generation, set it in your environment:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Notes

- Large files like PDFs are typically excluded from version control with .gitignore
- For development, each contributor should place their own copy of the PDF here
- In production, only the generated vector indices are needed, not the source PDF
