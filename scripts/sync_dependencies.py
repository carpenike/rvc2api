#!/usr/bin/env python3
"""
Dependency Synchronization Script

Synchronizes Python dependencies between pyproject.toml and flake.nix to prevent
CI failures caused by missing dependencies in the Nix package definition.

This script handles the common name mapping issues between PyPI and nixpkgs:
- PyYAML → pyyaml
- prometheus-client → prometheus_client
- python-dotenv → python-dotenv (same)
- etc.

Usage:
    poetry run python scripts/sync_dependencies.py [--dry-run] [--check]

Options:
    --dry-run: Show what would be changed without modifying files
    --check: Exit with error if dependencies are out of sync
"""

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import ClassVar


class DependencyMapper:
    """Maps PyPI package names to nixpkgs Python package names."""

    EXPLICIT_MAPPINGS: ClassVar[dict[str, str]] = {
        # Common naming differences
        "PyYAML": "pyyaml",
        "prometheus-client": "prometheus_client",
        "python-dotenv": "python-dotenv",
        "python-can": "python-can",
        "langchain-core": "langchain-core",
        "langchain-community": "langchain-community",
        # Handle package extras
        "uvicorn[standard]": "uvicorn",  # Map uvicorn[standard] to uvicorn
        # Potential future mappings
        "Pillow": "pillow",
        "beautifulsoup4": "beautifulsoup4",
        "requests-oauthlib": "requests-oauthlib",
        "python-multipart": "python-multipart",
    }

    # Dependencies that are allowed to be in flake.nix but not in pyproject.toml
    # These are typically dependencies of other packages or Nix-specific requirements
    ALLOWED_EXTRA_NIX_DEPS: ClassVar[set[str]] = {
        # uvicorn[standard] dependencies
        "httptools",
        "watchfiles",
        "websockets",
        "uvicorn",
        # Other Nix-specific or indirect dependencies
        "python-dotenv",  # Used by uvicorn for .env loading
        "httpx",  # Used by FastAPI for testing and HTTP requests
        # Extra dependencies that might have been removed from pyproject.toml
        # but are still needed for functionality
        "langchain-core",  # Dependency of langchain-community
    }

    @classmethod
    def pypi_to_nixpkgs(cls, pypi_name: str) -> str:
        """Convert PyPI package name to nixpkgs name, using explicit mappings and heuristics."""
        if pypi_name in cls.EXPLICIT_MAPPINGS:
            return cls.EXPLICIT_MAPPINGS[pypi_name]
        # Heuristic: lowercase and replace hyphens with underscores
        return pypi_name.lower().replace("-", "_")

    @staticmethod
    def validate_nixpkgs_package(pkg_name: str) -> bool:
        """Check if a Python package exists in nixpkgs (python3Packages)."""
        try:
            result = subprocess.run(
                [
                    "nix",
                    "eval",
                    f"nixpkgs#python3Packages.{pkg_name}",
                    "--raw",
                ],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False


class FlakeNixUpdater:
    """Updates flake.nix with Python dependencies."""

    def __init__(self, flake_path: Path):
        self.flake_path = flake_path

    def read_current_dependencies(self) -> set[str]:
        """
        Read the current propagatedBuildInputs dependencies from flake.nix.

        Returns:
            set[str]: Set of dependency names (without pythonPackages. prefix)
        """
        content = self.flake_path.read_text()
        # Find the propagatedBuildInputs section
        pattern = r"propagatedBuildInputs\s*=\s*\[(.*?)\]"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return set()
        deps_text = match.group(1)
        # Extract pythonPackages.* entries
        pkg_pattern = r"pythonPackages\.([a-zA-Z0-9_-]+)"
        packages = re.findall(pkg_pattern, deps_text)
        return set(packages)

    def update_dependencies(self, new_deps: set[str], dry_run: bool = False) -> bool:
        """
        Update flake.nix with new dependencies.

        Args:
            new_deps: Set of dependency names to include
            dry_run: If True, show what would be changed without modifying files

        Returns:
            bool: True if successful, False otherwise
        """
        content = self.flake_path.read_text()
        # Find propagatedBuildInputs section
        pattern = r"(propagatedBuildInputs\s*=\s*\[)(.*?)(\])"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            print("❌ Could not find propagatedBuildInputs section in flake.nix")
            return False
        # Build new dependency list
        deps_list = [f"            pythonPackages.{dep}" for dep in sorted(new_deps)]
        # Handle conditional dependencies (preserve existing structure)
        conditional_deps = []
        # Extract existing conditional sections
        existing_content = match.group(2)
        # Look for conditional patterns
        conditional_patterns = [
            r"(\s*\]\s*\+\+\s*pkgs\.lib\.optionals.*?\[.*?\])",
        ]
        for cond_pattern in conditional_patterns:
            matches = re.findall(cond_pattern, existing_content, re.DOTALL)
            conditional_deps.extend(matches)
        # Build new content
        new_deps_section = "\n" + "\n".join(deps_list)
        # Add conditional dependencies
        if conditional_deps:
            new_deps_section += "\n" + "\n".join(conditional_deps)
        new_content = (
            content[: match.start(1) + len(match.group(1))]
            + new_deps_section
            + "\n        "
            + content[match.end(3) :]
        )
        if dry_run:
            print("[DRY RUN] Would update flake.nix with the following dependencies:")
            print(new_deps_section)
            return True
        try:
            self.flake_path.write_text(new_content)
            print("✅ flake.nix dependencies updated.")
            return True
        except Exception as e:
            print(f"❌ Failed to write flake.nix: {e}")
            return False


class PyprojectParser:
    """Parses dependencies from pyproject.toml."""

    def __init__(self, pyproject_path: Path):
        self.pyproject_path = pyproject_path

    def get_dependencies(self) -> set[str]:
        """Extract main dependencies from pyproject.toml."""
        with open(self.pyproject_path, "rb") as f:
            data = tomllib.load(f)

        dependencies = set()

        # Get main dependencies
        project_deps = data.get("project", {}).get("dependencies", [])
        for dep in project_deps:
            # Parse dependency specification (name>=version, name==version, etc.)
            name = re.split(r"[>=<!=~]", dep)[0].strip()
            dependencies.add(name)

        # Get tool.poetry dependencies (if using Poetry format)
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for name, _spec in poetry_deps.items():
            if name != "python":  # Skip Python version constraint
                dependencies.add(name)

        return dependencies


def main() -> None:
    """Main entry point for the dependency sync script."""
    parser = argparse.ArgumentParser(
        description="Synchronize Python dependencies between pyproject.toml and flake.nix.",
        epilog="Example: poetry run python scripts/sync_dependencies.py --dry-run",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying them."
    )
    parser.add_argument(
        "--check", action="store_true", help="Check if sync is needed and exit with error code."
    )
    args = parser.parse_args()

    # Paths
    workspace_root = Path(__file__).parent.parent
    pyproject_path = workspace_root / "pyproject.toml"
    flake_path = workspace_root / "flake.nix"

    if not pyproject_path.exists():
        print(f"❌ pyproject.toml not found at {pyproject_path}")
        sys.exit(1)

    if not flake_path.exists():
        print(f"❌ flake.nix not found at {flake_path}")
        sys.exit(1)

    # Parse dependencies
    print("📋 Reading dependencies from pyproject.toml...")
    pyproject_parser = PyprojectParser(pyproject_path)
    pypi_deps = pyproject_parser.get_dependencies()

    print(f"   Found {len(pypi_deps)} dependencies: {', '.join(sorted(pypi_deps))}")

    # Map to nixpkgs names
    print("🔄 Mapping PyPI names to nixpkgs names...")
    nixpkgs_deps = set()
    validation_failures = []

    for dep in pypi_deps:
        nix_name = DependencyMapper.pypi_to_nixpkgs(dep)

        # Validate package exists in nixpkgs
        if DependencyMapper.validate_nixpkgs_package(nix_name):
            nixpkgs_deps.add(nix_name)
            print(f"   ✅ {dep} → {nix_name}")
        else:
            validation_failures.append((dep, nix_name))
            print(f"   ⚠️  {dep} → {nix_name} (package not found in nixpkgs)")

    # Read current flake.nix dependencies
    print("📖 Reading current dependencies from flake.nix...")
    flake_updater = FlakeNixUpdater(flake_path)
    current_nix_deps = flake_updater.read_current_dependencies()

    print(f"   Found {len(current_nix_deps)} dependencies: {', '.join(sorted(current_nix_deps))}")

    # Compare dependencies
    missing_in_nix = nixpkgs_deps - current_nix_deps
    raw_extra_in_nix = current_nix_deps - nixpkgs_deps

    # Filter out allowed extra dependencies
    extra_in_nix = raw_extra_in_nix - DependencyMapper.ALLOWED_EXTRA_NIX_DEPS
    allowed_extras = raw_extra_in_nix & DependencyMapper.ALLOWED_EXTRA_NIX_DEPS

    print("\n📊 Dependency Analysis:")
    print(f"   Dependencies in sync: {len(nixpkgs_deps & current_nix_deps)}")
    print(f"   Missing from flake.nix: {len(missing_in_nix)}")
    print(f"   Extra in flake.nix: {len(extra_in_nix)}")
    print(f"   Allowed extras in flake.nix: {len(allowed_extras)}")
    print(f"   Validation failures: {len(validation_failures)}")

    if missing_in_nix:
        print(f"\n❌ Missing from flake.nix: {', '.join(sorted(missing_in_nix))}")

    if allowed_extras:
        print(f"\n✅ Allowed extra dependencies in flake.nix: {', '.join(sorted(allowed_extras))}")

    if extra_in_nix:
        print(f"\n⚠️  Unexpected extra in flake.nix: {', '.join(sorted(extra_in_nix))}")

    if validation_failures:
        print("\n⚠️  Could not validate in nixpkgs:")
        for pypi_name, nix_name in validation_failures:
            print(f"     {pypi_name} → {nix_name}")
        print("   These may need manual mapping or might not be available in nixpkgs")

    # Check mode
    if args.check:
        if missing_in_nix or validation_failures or extra_in_nix:  # Only fail for unexpected extras
            print("\n❌ Dependencies are out of sync!")
            sys.exit(1)
        else:
            print("\n✅ Dependencies are in sync!")
            sys.exit(0)

    # Update flake.nix
    if missing_in_nix:
        print(f"\n🔧 {'Would update' if args.dry_run else 'Updating'} flake.nix...")

        # Merge current dependencies with new ones
        updated_deps = current_nix_deps | nixpkgs_deps

        success = flake_updater.update_dependencies(updated_deps, dry_run=args.dry_run)

        if success and not args.dry_run:
            print("✅ flake.nix updated successfully!")
            print("\n🚀 Next steps:")
            print("   1. Review the changes: git diff flake.nix")
            print("   2. Test the build: nix build")
            print("   3. Test CI locally: nix run .#ci")
        elif success and args.dry_run:
            print("✅ Dry run completed successfully!")
        else:
            print("❌ Failed to update flake.nix")
            sys.exit(1)
    else:
        print("\n✅ No updates needed!")

    if validation_failures:
        print(f"\n⚠️  Manual attention needed for {len(validation_failures)} packages")
        print("   Check if these packages exist in nixpkgs with different names")
        print("   or if they need to be added to the explicit mappings")


if __name__ == "__main__":
    main()
