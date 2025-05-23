#!/usr/bin/env python3
"""
Dependency Analyzer Script

This script analyzes the project's dependencies, detects unused dependencies using deptry,
and can optionally remove them from pyproject.toml. It is intended to help maintain a clean
dependency set for the project.

Usage:
    poetry run python scripts/detect_unused_dependencies.py
    poetry run python scripts/detect_unused_dependencies.py --check
    poetry run python scripts/detect_unused_dependencies.py --dry-run
    poetry run python scripts/detect_unused_dependencies.py --fix

Returns:
    Used and unused dependencies, and can update pyproject.toml if requested.
"""

import argparse
import logging
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, ClassVar

import toml


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the script.

    Args:
        verbose: If True, set log level to DEBUG, else INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
    )


class DependencyAnalyzer:
    """
    Analyzes and detects unused dependencies in a Python project.
    """

    IGNORE_PACKAGES: ClassVar[set[str]] = {
        # Common false positives or packages that are used implicitly
        "uvicorn",
        "websockets",
        "httptools",
        "python-dotenv",
        "watchfiles",
        "uvloop",
        "prometheus_client",
        "coloredlogs",
        # Add other packages that might be false positives here
    }

    def __init__(self, pyproject_path: Path):
        self.pyproject_path = pyproject_path
        self.src_dir = pyproject_path.parent / "src"

    def get_project_dependencies(self) -> tuple[set[str], dict[str, Any]]:
        """
        Extract all dependencies from pyproject.toml.

        Returns:
            A tuple of (set of dependency names, full pyproject data dict).
        """
        logging.info(f"Reading dependencies from {self.pyproject_path}")
        with open(self.pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        dependencies = set()

        # Get main dependencies
        project_deps = pyproject_data.get("project", {}).get("dependencies", [])
        logging.debug(f"Project dependencies (raw): {project_deps}")
        for dep in project_deps:
            name = re.split(r"[>=<!=~]", dep)[0].strip()
            dependencies.add(name)
            logging.debug(f"Added dependency: {name}")

        # Get tool.poetry dependencies (if using Poetry format)
        poetry_deps = pyproject_data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        logging.debug(f"Poetry dependencies (raw): {list(poetry_deps.keys())}")
        for name, _spec in poetry_deps.items():
            if name != "python":
                dependencies.add(name)
                logging.debug(f"Added poetry dependency: {name}")

        return dependencies, pyproject_data

    def run_deptry(self) -> set[str] | None:
        """
        Run deptry to detect unused dependencies.

        Returns:
            Set[str] | None: Set of unused dependency names, or None if deptry failed.

        Example:
            >>> analyzer = DependencyAnalyzer()
            >>> unused = analyzer.run_deptry()
            >>> print(unused)
            {'requests', 'pytest'}
        """
        logging.info("🔍 Running deptry to detect unused dependencies...")
        try:
            result = subprocess.run(
                ["poetry", "run", "deptry", "."],
                capture_output=True,
                text=True,
                check=False,
            )
            logging.debug(f"Deptry completed with return code: {result.returncode}")
            stderr_lines = result.stderr.strip().splitlines() if result.stderr else []
            stdout_lines = result.stdout.strip().splitlines() if result.stdout else []
            unused_deps = set()
            # Parse both stdout and stderr for DEP002 lines
            for line in stdout_lines + stderr_lines:
                # Example deptry output: DEP002 Unused dependency 'requests' (defined as a dependency but not used)
                if "DEP002" in line and "defined as a dependency but not used" in line:
                    parts = line.split("'")
                    if len(parts) > 1:
                        dep_name = parts[1]
                        unused_deps.add(dep_name)
            return unused_deps
        except Exception as e:
            logging.error(f"Failed to run deptry: {e}")
            return None

    def analyze(self) -> tuple[set[str], set[str]]:
        """
        Analyze the project for unused dependencies.

        Returns:
            tuple[set[str], set[str]]: (used_deps, unused_deps)

        Example:
            >>> analyzer = DependencyAnalyzer()
            >>> used, unused = analyzer.analyze()
            >>> print(f"Used: {used}, Unused: {unused}")
        """
        logging.info("Starting analyze method...")
        all_deps, _ = self.get_project_dependencies()
        logging.info(f"Found {len(all_deps)} dependencies in pyproject.toml: {all_deps}")

        unused_deps = self.run_deptry() or set()
        logging.info(f"Deptry found {len(unused_deps)} unused dependencies: {unused_deps}")

        # Filter out ignored packages
        filtered_unused_deps = unused_deps - self.IGNORE_PACKAGES
        logging.info(
            f"After filtering, {len(filtered_unused_deps)} unused dependencies remain: {filtered_unused_deps}"
        )

        used_deps = all_deps - filtered_unused_deps
        logging.info(f"Used dependencies: {len(used_deps)} - {used_deps}")

        return used_deps, filtered_unused_deps

    def remove_unused_dependencies(self, unused_deps: set[str], dry_run: bool = False) -> bool:
        """
        Remove unused dependencies from pyproject.toml.

        Args:
            unused_deps (set[str]): Set of dependency names to remove
            dry_run (bool): If True, show what would be changed without modifying files

        Returns:
            bool: True if successful, False otherwise

        Example:
            >>> analyzer = DependencyAnalyzer()
            >>> _, unused = analyzer.analyze()
            >>> analyzer.remove_unused_dependencies(unused, dry_run=True)
        """
        if not unused_deps:
            logging.info("No unused dependencies to remove.")
            return True

        # Load with toml library for writing
        with open(self.pyproject_path) as f:
            pyproject_data = toml.load(f)

        # Remove from project.dependencies
        if "project" in pyproject_data and "dependencies" in pyproject_data["project"]:
            project_deps = pyproject_data["project"]["dependencies"]
            new_project_deps = []

            for dep in project_deps:
                # Parse dependency name
                name = re.split(r"[>=<!=~]", dep)[0].strip()
                if name not in unused_deps:
                    new_project_deps.append(dep)
                else:
                    logging.info(f"Removing unused dependency from [project.dependencies]: {dep}")

            pyproject_data["project"]["dependencies"] = new_project_deps

        # Remove from tool.poetry.dependencies
        if (
            "tool" in pyproject_data
            and "poetry" in pyproject_data["tool"]
            and "dependencies" in pyproject_data["tool"]["poetry"]
        ):
            poetry_deps = pyproject_data["tool"]["poetry"]["dependencies"]
            for dep in list(poetry_deps.keys()):
                if dep in unused_deps:
                    logging.info(
                        f"Removing unused dependency from [tool.poetry.dependencies]: {dep}"
                    )
                    poetry_deps.pop(dep)

        if dry_run:
            logging.info("Dry run enabled. No changes written to pyproject.toml.")
            return True

        # Write changes back to pyproject.toml
        try:
            with open(self.pyproject_path, "w") as f:
                toml.dump(pyproject_data, f)
            logging.info("Unused dependencies removed from pyproject.toml.")
            return True
        except Exception as e:
            logging.error(f"Failed to write changes to pyproject.toml: {e}")
            return False


def main() -> None:
    """
    Main entry point for the unused dependency detection script.
    """
    parser = argparse.ArgumentParser(
        description="Detect and optionally remove unused dependencies from pyproject.toml."
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically remove unused dependencies."
    )
    parser.add_argument(
        "--check", action="store_true", help="Exit with error if unused dependencies are found."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be changed without modifying files."
    )
    parser.add_argument(
        "--pyproject", type=str, default="pyproject.toml", help="Path to pyproject.toml."
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output.")
    args = parser.parse_args()

    setup_logging(args.verbose)

    pyproject_path = Path(args.pyproject).resolve()
    if not pyproject_path.exists():
        logging.error(f"pyproject.toml not found at {pyproject_path}")
        sys.exit(2)

    analyzer = DependencyAnalyzer(pyproject_path)
    all_deps, pyproject_data = analyzer.get_project_dependencies()
    unused_deps = analyzer.run_deptry()
    if unused_deps is None:
        logging.error("Deptry failed. Aborting.")
        sys.exit(3)
    if not unused_deps:
        logging.info("No unused dependencies found! 🎉")
        sys.exit(0)

    logging.warning(f"Unused dependencies detected: {sorted(unused_deps)}")

    if args.dry_run:
        print("[DRY RUN] The following dependencies would be removed:")
        for dep in sorted(unused_deps):
            print(f"  - {dep}")
        sys.exit(1)

    if args.check:
        print("Unused dependencies found:")
        for dep in sorted(unused_deps):
            print(f"  - {dep}")
        sys.exit(1)

    if args.fix:
        # Remove unused dependencies from pyproject.toml
        print("Removing unused dependencies from pyproject.toml...")
        updated = False
        # Remove from [project] dependencies
        project_deps = pyproject_data.get("project", {}).get("dependencies", [])
        new_project_deps = [
            dep for dep in project_deps if re.split(r"[>=<!=~]", dep)[0].strip() not in unused_deps
        ]
        if len(new_project_deps) != len(project_deps):
            pyproject_data["project"]["dependencies"] = new_project_deps
            updated = True
        # Remove from [tool.poetry.dependencies]
        poetry_deps = pyproject_data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        for dep in unused_deps:
            if dep in poetry_deps:
                del poetry_deps[dep]
                updated = True
        if updated:
            with open(pyproject_path, "w", encoding="utf-8") as f:
                toml.dump(pyproject_data, f)
            print("Unused dependencies removed. Please run 'poetry update' to sync lock file.")
            sys.exit(0)
        else:
            print("No changes made to pyproject.toml.")
            sys.exit(0)
    # Default: just print unused dependencies
    print("Unused dependencies:")
    for dep in sorted(unused_deps):
        print(f"  - {dep}")
    sys.exit(1)


if __name__ == "__main__":
    main()
