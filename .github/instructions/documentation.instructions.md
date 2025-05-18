---
applyTo: "**/*.md"
---

# Documentation Guidelines

This file provides guidelines for documenting the `rvc2api` project, including API documentation, architecture documentation, and MkDocs configuration.

## API Documentation

### FastAPI Routes Documentation

All API endpoints require comprehensive documentation with examples, descriptions, and response schemas to maintain the OpenAPI specification:

````python
@router.get(
    "/entities",
    response_model=List[EntityResponse],
    summary="Get all entities",
    description="Returns a list of all available entities in the system.",
    response_description="List of entity objects with their properties",
    tags=["Entities"]
)
async def get_entities():
    """
    Get all entities in the system.

    This endpoint provides a list of all entities regardless of their state.
    Each entity contains properties like id, name, type, and state.

    Returns:
        List[EntityResponse]: A list of entity objects

    Examples:
        ```json
        [
            {
                "id": "light_123",
                "name": "Main Light",
                "type": "light",
                "state": {
                    "on": true,
                    "brightness": 100
                },
                "zone": "living_room"
            }
        ]
        ```
    """
    # Implementation
````

### Documentation Requirements

- **Route Summary**: A brief one-line description of the endpoint
- **Route Description**: More detailed explanation of what the endpoint does
- **Response Description**: What the response contains
- **Tags**: Appropriate categorization tags
- **Docstring**: Google-style docstring including:
  - General description
  - Parameters explanation
  - Return type and description
  - Examples with JSON payloads

## MkDocs Documentation Structure

The documentation is built with MkDocs using the Material theme, with the following structure:

- `/docs/mkdocs.yml`: Main configuration file
- `/docs/index.md`: Main landing page
- `/docs/api/`: API documentation
  - `overview.md`: API overview
  - `entities.md`: Entity endpoints documentation
  - `can.md`: CAN bus endpoints documentation
  - `websocket.md`: WebSocket API documentation
  - `openapi.md`: OpenAPI integration guide
  - `frontend-integration.md`: Using API from the frontend
- `/docs/architecture/`: Architecture documentation
  - `backend.md`: Backend architecture
  - `frontend.md`: Frontend architecture
  - `overview.md`: System overview
- `/docs/contributing/`: Contribution guidelines
  - `documentation.md`: How to contribute to docs
  - `openapi.md`: OpenAPI usage guide

## OpenAPI Schema Integration

The OpenAPI schema is automatically exported from FastAPI using the `scripts/export_openapi.py` script:

```python
# Example excerpt from export_openapi.py
from fastapi.openapi.utils import get_openapi
import json
import yaml
from pathlib import Path

def export_openapi():
    # Get OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Write JSON
    Path("docs/api/openapi.json").write_text(
        json.dumps(openapi_schema, indent=2)
    )

    # Write YAML
    Path("docs/api/openapi.yaml").write_text(
        yaml.dump(openapi_schema)
    )
```

## Frontend Type Generation

TypeScript types are generated from the OpenAPI schema using the script at `web_ui/scripts/generate-api-types.js`:

```javascript
// Example of the TypeScript type generation script
import { generateApi } from "swagger-typescript-api";
import path from "path";
import fs from "fs";

generateApi({
  name: "api.ts",
  output: path.resolve(process.cwd(), "./src/api"),
  url: path.resolve(process.cwd(), "../docs/api/openapi.json"),
  httpClientType: "fetch",
});
```

## VS Code Tasks for Documentation

The following VS Code tasks are available for working with documentation:

| Task Name                     | Description                              | Command                                                                  |
| ----------------------------- | ---------------------------------------- | ------------------------------------------------------------------------ |
| `Server: Serve Documentation` | Preview documentation with mkdocs serve  | `cd docs && mkdocs serve`                                                |
| `Build: Documentation`        | Build documentation                      | `cd docs && mkdocs build`                                                |
| `API: Export OpenAPI Schema`  | Export OpenAPI schema to JSON/YAML files | `poetry run python scripts/export_openapi.py`                            |
| `API: Update Documentation`   | Export OpenAPI schema and rebuild docs   | `poetry run python scripts/export_openapi.py && cd docs && mkdocs build` |

## Documentation Workflow

1. **Update API Endpoint Documentation**:

   - Add comprehensive docstrings to FastAPI routes
   - Include examples, descriptions, and response models

2. **Export OpenAPI Schema**:

   - Run VS Code task `API: Export OpenAPI Schema` or manually run `scripts/export_openapi.py`

3. **Generate Frontend Types** (if needed):

   - Run `cd web_ui && npm run generate:api-types`

4. **Build Documentation**:

   - Run VS Code task `Build: Documentation` or `cd docs && mkdocs build`

5. **Preview Documentation**:
   - Run VS Code task `Server: Serve Documentation` or `cd docs && mkdocs serve`
   - Open http://localhost:8000 in your browser

## Best Practices

- **Keep Documentation Close to Code**: Documentation should be as close as possible to the code it documents.
- **Update Documentation with Code Changes**: Always update relevant documentation when making code changes.
- **Use Descriptive and Complete Examples**: Provide realistic examples in API documentation.
- **Follow Consistent Structure**: Use the established structure for new documentation.
- **Test Documentation Accuracy**: Validate that examples and descriptions are accurate.
- **Write for the Target Audience**: Keep in mind who will be using the documentation (e.g., frontend developers, API users).

## See Also

- [VS Code Tasks](vscode-tasks.instructions.md)
- [Python Code Style](python-code-style.instructions.md)
- [MCP Tools](mcp-tools.instructions.md)
