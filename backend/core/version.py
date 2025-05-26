"""
Backend version information.

Provides version information for the backend application.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to get version from pyproject.toml
try:
    import tomllib

    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        VERSION = pyproject_data.get("project", {}).get("version", "unknown")
    else:
        VERSION = "unknown"

except Exception as e:
    logger.warning(f"Could not determine version from pyproject.toml: {e}")
    VERSION = "unknown"

__all__ = ["VERSION"]
