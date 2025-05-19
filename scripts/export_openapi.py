#!/usr/bin/env python3
"""
Script to export the OpenAPI schema from the rvc2api FastAPI application.

This script initializes the FastAPI app and exports its OpenAPI schema to a file
in both JSON and YAML formats. The exported schema can be:
1. Used by documentation tools
2. Imported into Swagger UI or other API exploration tools
3. Used by code generators to create client libraries
"""
import json
import sys
from pathlib import Path

import yaml


def setup_python_path():
    """Add the src directory to the python path."""
    # Get the directory of this script
    script_dir = Path(__file__).resolve().parent

    # Add the src directory to the path
    src_dir = str(script_dir.parent.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"Added {src_dir} to PYTHONPATH")


def export_openapi_schema():
    """
    Initialize the FastAPI app and export its OpenAPI schema to files.

    Saves the schema in both JSON and YAML formats in the docs directory.
    """
    from core_daemon.main import create_app

    # Create the FastAPI app
    print("Initializing FastAPI app...")
    app = create_app()

    # Get the OpenAPI schema
    print("Generating OpenAPI schema...")
    openapi_schema = app.openapi()

    # Create the output directory if it doesn't exist
    docs_api_dir = Path(__file__).parent.parent / "docs" / "api"
    docs_api_dir.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    json_path = docs_api_dir / "openapi.json"
    with open(json_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Saved OpenAPI schema as JSON to {json_path}")

    # Save as YAML
    yaml_path = docs_api_dir / "openapi.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False)
    print(f"Saved OpenAPI schema as YAML to {yaml_path}")

    return openapi_schema


if __name__ == "__main__":
    # Setup the python path to find the required modules
    setup_python_path()

    # Export the OpenAPI schema
    openapi_schema = export_openapi_schema()

    # Print some basic stats
    endpoint_count = sum(len(methods) for path, methods in openapi_schema["paths"].items())
    model_count = (
        len(openapi_schema["components"]["schemas"])
        if "schemas" in openapi_schema["components"]
        else 0
    )

    print("\nSuccessfully exported OpenAPI schema with:")
    print(f"  - {endpoint_count} endpoints")
    print(f"  - {model_count} models")
    print("\nYou can now use this schema for documentation or code generation.")
