# OpenAPI Specification

The rvc2api service provides a comprehensive OpenAPI specification that documents all available API endpoints, request parameters, response formats, and data models.

## What is OpenAPI?

OpenAPI (formerly known as Swagger) is a specification for machine-readable interface files for describing, producing, consuming, and visualizing RESTful web services. The OpenAPI specification defines a standard, language-agnostic interface to RESTful APIs.

## How to Access the OpenAPI Specification

### Interactive Documentation

The FastAPI framework automatically generates interactive API documentation based on the OpenAPI specification. You can access it directly in your browser while the server is running:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Raw OpenAPI Schema

You can also access the raw OpenAPI schema in JSON format:

- **JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

For convenience, the OpenAPI schema is also exported to files in the `docs/api` directory:

- `openapi.json` - JSON format
- `openapi.yaml` - YAML format

## Generating API Clients

You can use the OpenAPI schema to generate client libraries for various programming languages using tools like:

- [openapi-generator](https://openapi-generator.tech/)
- [Swagger Codegen](https://swagger.io/tools/swagger-codegen/)

### Example: Generating a TypeScript Client

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate a TypeScript client
openapi-generator-cli generate -i docs/api/openapi.json -g typescript-fetch -o frontend/src/api/generated
```

### Example: Generating a Python Client

```bash
# Install OpenAPI Generator
pip install openapi-generator-cli

# Generate a Python client
openapi-generator-cli generate -i docs/api/openapi.json -g python -o clients/python
```

## Using the OpenAPI Schema for Documentation

The OpenAPI schema is integrated with this documentation site. You can find the complete API reference in the API section of this documentation.

You can also import the OpenAPI schema into tools like:

- [Postman](https://www.postman.com/)
- [Insomnia](https://insomnia.rest/)
- [Stoplight Studio](https://stoplight.io/studio/)

This allows you to explore and test the API without writing any code.

## Keeping the OpenAPI Schema Up-to-Date

The OpenAPI schema is automatically generated from the API code. To manually update the exported files, run:

```bash
cd /Users/ryan/src/rvc2api
poetry run python scripts/export_openapi.py
```

This will regenerate the `docs/api/openapi.json` and `docs/api/openapi.yaml` files.
