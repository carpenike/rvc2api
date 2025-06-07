# Using OpenAPI in Development

This guide explains how to use the OpenAPI schema in your development workflow for both frontend and backend development.

## What is OpenAPI?

OpenAPI is a specification for describing RESTful APIs. It provides a standardized way to document API endpoints, request parameters, response formats, and data models.

FastAPI automatically generates an OpenAPI schema based on your route definitions, type hints, and docstrings. This schema can be used to:

1. Generate interactive API documentation
2. Create API client libraries
3. Validate API requests and responses
4. Generate mock data for testing

## Accessing the OpenAPI Schema

### Interactive Documentation

When the rvc2api server is running, you can access the interactive API documentation at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Raw Schema

You can also access the raw OpenAPI schema in JSON format:

- **JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Exported Schema Files

The OpenAPI schema is also exported to files in the `docs/api` directory:

- `openapi.json` - JSON format
- `openapi.yaml` - YAML format

To update these files, run:

```bash
poetry run python scripts/export_openapi.py
```

Or use the VS Code task "API: Export OpenAPI Schema".

## Frontend Development with OpenAPI

### Generating TypeScript Types

You can generate TypeScript types from the OpenAPI schema using tools like `openapi-typescript`:

```bash
# Install the tool
npm install --save-dev openapi-typescript

# Generate types
npx openapi-typescript docs/api/openapi.json --output frontend/src/api/generated/types.ts
```

This ensures that your frontend code uses types that are consistent with the backend API.

### Generating API Clients

You can also generate a full TypeScript client for the API:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate a TypeScript client
openapi-generator-cli generate -i docs/api/openapi.json -g typescript-fetch -o frontend/src/api/generated
```

This client provides type-safe methods for all API endpoints.

## Backend Development with OpenAPI

### Documenting Endpoints

To ensure that your API endpoints are properly documented in the OpenAPI schema, follow these practices:

#### Route Decorators

Use the full range of FastAPI route decorators:

```python
@router.get(
    "/entities",
    response_model=dict[str, Entity],
    summary="List all entities",
    description="Retrieve all entities with optional filtering by device type or area.",
    response_description="A dictionary of entities matching the filter criteria.",
    tags=["entities"]
)
```

#### Parameter Documentation

Document all parameters:

```python
async def list_entities(
    device_type: str | None = Query(
        None,
        description="Filter entities by device type (e.g., 'light', 'tank', 'temperature')"
    ),
    area: str | None = Query(
        None,
        description="Filter entities by suggested area (e.g., 'living', 'bedroom', 'bathroom')"
    ),
):
    """
    Return all entities, optionally filtered by device_type and/or area.
    ...
    """
```

#### Response Examples

Provide examples for requests and responses using FastAPI's example system:

```python
@router.post(
    "/entities/{entity_id}/control",
    response_model=ControlEntityResponse,
)
async def control_entity(
    entity_id: str,
    cmd: Annotated[
        ControlCommand,
        Body(
            examples={
                "turn_on": {"summary": "Turn light on", "value": {"command": "set", "state": "on"}},
                "turn_off": {"summary": "Turn light off", "value": {"command": "set", "state": "off"}},
            }
        ),
    ],
):
    """Control a light entity based on the provided command."""
```

### Testing Against the Schema

You can validate your API implementation against the OpenAPI schema using tools like `openapi-python-client`:

```bash
pip install openapi-python-client

# Generate a client
openapi-python-client generate --url http://localhost:8000/openapi.json --output api_client

# Use the client in tests
```

## OpenAPI Integration Tools

### VS Code Extensions

- **OpenAPI (Swagger) Editor**: Provides syntax highlighting and validation for OpenAPI files
- **Swagger Viewer**: Preview OpenAPI schemas in VS Code

### Postman Integration

You can import the OpenAPI schema into Postman:

1. In Postman, click "Import"
2. Select "OpenAPI"
3. Choose the `openapi.json` file or enter the URL `http://localhost:8000/openapi.json`

This will create a collection with all API endpoints, making it easy to test and explore the API.

### Continuous Integration

To ensure that your OpenAPI schema stays up-to-date with your code, add the following steps to your CI pipeline:

1. Generate the OpenAPI schema
2. Compare it with the committed version
3. Fail if there are differences

This ensures that your documentation always matches your implementation.
