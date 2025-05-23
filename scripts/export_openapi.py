#!/usr/bin/env python3
"""
Script to export the OpenAPI schema from the rvc2api FastAPI application.

This script initializes the FastAPI app and exports its OpenAPI schema to a file
in both JSON and YAML formats. The exported schema can be:
1. Used by documentation tools
2. Imported into Swagger UI or other API exploration tools
3. Used by code generators to create client libraries

Usage:
    poetry run python scripts/export_openapi.py [output_dir]
    # output_dir defaults to ../docs/api relative to this script
"""
import json
import sys
import traceback
from pathlib import Path

import yaml


def setup_python_path():
    """Add the src directory to the python path."""
    script_dir = Path(__file__).resolve().parent
    src_dir = str(script_dir.parent / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"Added {src_dir} to PYTHONPATH")


def export_openapi_schema(output_dir: Path) -> int:
    """
    Initialize the FastAPI app and export its OpenAPI schema to files.
    Saves the schema in both JSON and YAML formats in the output directory.
    Returns 0 on success, 1 on failure.
    """
    try:
        setup_python_path()
        try:
            from core_daemon.main import create_app
        except Exception:
            print("[ERROR] Could not import create_app from core_daemon.main:")
            traceback.print_exc()
            return 1
        print("Initializing FastAPI app...")
        try:
            app = create_app()
        except Exception:
            print("[ERROR] Could not create FastAPI app:")
            traceback.print_exc()
            return 1
        print("Generating OpenAPI schema...")
        try:
            openapi_schema = app.openapi()  # type: ignore[attr-defined]
        except Exception:
            print("[ERROR] Could not generate OpenAPI schema:")
            traceback.print_exc()
            return 1
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "openapi.json"
        with open(json_path, "w") as f:
            json.dump(openapi_schema, f, indent=2)
        print(f"Saved OpenAPI schema as JSON to {json_path}")
        yaml_path = output_dir / "openapi.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(openapi_schema, f, sort_keys=False, allow_unicode=True)
        print(f"Saved OpenAPI schema as YAML to {yaml_path}")
        print("OpenAPI export completed successfully.")
        return 0
    except Exception:
        print("[FATAL ERROR] Unexpected error during OpenAPI export:")
        traceback.print_exc()
        return 1


def main():
    # Allow output directory override via CLI
    default_output = Path(__file__).parent.parent / "docs" / "api"
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default_output
    exit_code = export_openapi_schema(output_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
