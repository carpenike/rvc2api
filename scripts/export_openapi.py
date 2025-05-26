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


def setup_python_path() -> None:
    """
    Add the backend directory to the Python path if not already present.
    """
    script_dir = Path(__file__).resolve().parent
    backend_dir = str(script_dir.parent)  # Root directory containing backend/
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
        print(f"[INFO] Added {backend_dir} to PYTHONPATH")


def export_openapi_schema(output_dir: Path) -> int:
    """
    Initialize the FastAPI app and export its OpenAPI schema to files.

    Args:
        output_dir: Directory to write openapi.json and openapi.yaml

    Returns:
        0 on success, 1 on failure.
    """
    try:
        setup_python_path()
        try:
            from backend.main import create_app
        except Exception:
            print("[ERROR] Could not import create_app from backend.main:")
            traceback.print_exc()
            return 1
        print("[INFO] Initializing FastAPI app...")
        try:
            app = create_app()
        except Exception:
            print("[ERROR] Failed to initialize FastAPI app:")
            traceback.print_exc()
            return 1
        print("[INFO] Generating OpenAPI schema...")
        try:
            # Use FastAPI's get_openapi utility for robust schema export
            try:
                from fastapi.openapi.utils import get_openapi
            except ImportError:
                print("[ERROR] Could not import get_openapi from fastapi.openapi.utils.")
                traceback.print_exc()
                return 1
            # Use getattr with fallback defaults to avoid attribute errors
            openapi_schema = get_openapi(
                title=getattr(app, "title", "API"),
                version=getattr(app, "version", "0.1.0"),
                description=getattr(app, "description", "OpenAPI schema export"),
                routes=getattr(app, "routes", []),
            )
        except Exception:
            print("[ERROR] Failed to generate OpenAPI schema:")
            traceback.print_exc()
            return 1
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "openapi.json"
        yaml_path = output_dir / "openapi.yaml"
        try:
            with open(json_path, "w", encoding="utf-8") as f_json:
                json.dump(openapi_schema, f_json, indent=2, ensure_ascii=False)
            print(f"[INFO] Wrote OpenAPI JSON to {json_path}")
            with open(yaml_path, "w", encoding="utf-8") as f_yaml:
                yaml.dump(openapi_schema, f_yaml, sort_keys=False, allow_unicode=True)
            print(f"[INFO] Wrote OpenAPI YAML to {yaml_path}")
        except Exception:
            print("[ERROR] Failed to write OpenAPI schema files:")
            traceback.print_exc()
            return 1
        print("[SUCCESS] OpenAPI schema export complete.")
        return 0
    except Exception:
        print("[FATAL] Unexpected error during OpenAPI export:")
        traceback.print_exc()
        return 1


def main() -> None:
    """
    Main entry point for the script. Parses arguments and runs export.
    """
    default_output = Path(__file__).resolve().parent.parent / "docs" / "api"
    output_dir: Path | None = Path(sys.argv[1]).resolve() if (len(sys.argv) > 1) else default_output
    print(f"[INFO] Exporting OpenAPI schema to: {output_dir}")
    exit_code = export_openapi_schema(output_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
