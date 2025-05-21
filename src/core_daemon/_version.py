import importlib.metadata

try:
    VERSION = importlib.metadata.version("rvc2api")
except importlib.metadata.PackageNotFoundError:
    # Fallback for when the package is not installed (e.g., during development tests)
    # Read from the VERSION file directly as the source of truth
    try:
        from pathlib import Path

        version_file = Path(__file__).parents[2].parent / "VERSION"
        VERSION = version_file.read_text().strip()
    except (FileNotFoundError, OSError):
        # If VERSION file can't be read, use a placeholder
        VERSION = "0.0.0-dev"
