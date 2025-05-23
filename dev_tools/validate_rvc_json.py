"""
validate_rvc_json.py

Validation and optional auto-fix tool for rvc.json CANbus spec files.

- Ensures all PGN keys in 'pgns' are strings
- Ensures each signal has a 'byte_order' (defaults to 'big_endian' if missing)
- Optionally adds $schema and version fields
- Reports all issues found, or auto-fixes if --fix is passed

Usage:
  poetry run python dev_tools/validate_rvc_json.py /path/to/rvc.json [--fix] [--dry-run] [--backup] [--output OUTPUT] [--verbose]

Exits with code 0 if valid, 1 if errors found (unless --fix is used).
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA_URL = "/docs/schemas/rvc-schema.json"
SCHEMA_VERSION = date.today().isoformat()


def validate_and_fix_rvc_json(
    data: dict[str, Any], fix: bool = False, verbose: bool = False
) -> tuple[list[str], dict[str, Any]]:
    """Validate and optionally fix a rvc.json spec dict.

    Args:
        data: Parsed rvc.json as a dictionary.
        fix: If True, auto-fix issues in-place.
        verbose: If True, log detailed info.

    Returns:
        Tuple of (list of error messages, possibly fixed data dict).
    """
    errors: list[str] = []

    # Check for $schema and version
    if "$schema" not in data:
        errors.append("Missing $schema field at top level.")
        if fix:
            data["$schema"] = SCHEMA_URL
            if verbose:
                logging.info("Added missing $schema field.")
    if "version" not in data:
        errors.append("Missing version field at top level.")
        if fix:
            data["version"] = SCHEMA_VERSION
            if verbose:
                logging.info("Added missing version field.")

    # Check pgns
    pgns = data.get("pgns")
    if not isinstance(pgns, dict):
        errors.append("Top-level 'pgns' must be a dictionary.")
        return errors, data

    # Ensure all keys are strings
    for key in list(pgns.keys()):
        if not isinstance(key, str):
            errors.append(f"PGN key {key} is not a string.")
            if fix:
                pgns[str(key)] = pgns.pop(key)
                if verbose:
                    logging.info(f"Converted PGN key {key} to string.")

    # Validate each PGN's signals
    for pgn, pgn_data in pgns.items():
        signals = pgn_data.get("signals")
        if not isinstance(signals, list):
            errors.append(f"PGN {pgn}: 'signals' must be a list.")
            continue
        for idx, signal in enumerate(signals):
            if not isinstance(signal, dict):
                errors.append(f"PGN {pgn} signal {idx}: not a dict.")
                continue
            if "byte_order" not in signal:
                errors.append(f"PGN {pgn} signal {idx}: missing 'byte_order'.")
                if fix:
                    signal["byte_order"] = "big_endian"
                    if verbose:
                        logging.info(
                            f"PGN {pgn} signal {idx}: set default 'byte_order' to 'big_endian'."
                        )

    return errors, data


def backup_file(path: Path) -> Path:
    """Create a backup of the given file, returns backup path."""
    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and optionally auto-fix rvc.json CANbus spec files."
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to rvc.json file to validate.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues in-place (overwrites file unless --output is used).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed, but do not write changes.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup the original file before writing changes.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write fixed output to this file instead of overwriting input.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="[%(levelname)s] %(message)s",
    )

    try:
        with args.file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logging.error(f"Failed to load JSON: {exc}")
        sys.exit(1)

    errors, fixed_data = validate_and_fix_rvc_json(
        data, fix=args.fix or args.dry_run, verbose=args.verbose
    )

    if errors:
        logging.warning("Validation issues found:")
        for err in errors:
            logging.warning(f"  - {err}")
    else:
        logging.info("No validation issues found.")

    if (args.fix or args.dry_run) and errors:
        if args.dry_run:
            print("\n[DRY RUN] The following changes would be made:")
            print(json.dumps(fixed_data, indent=2, ensure_ascii=False))
            sys.exit(1)
        else:
            if args.backup:
                backup_path = backup_file(args.file)
                logging.info(f"Backup created at {backup_path}")
            output_path = args.output if args.output else args.file
            try:
                with output_path.open("w", encoding="utf-8") as f:
                    json.dump(fixed_data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                print(f"Fixed file written to {output_path}")
            except Exception as exc:
                logging.error(f"Failed to write fixed file: {exc}")
                sys.exit(1)
            sys.exit(0)
    elif errors:
        print("Validation failed. Run with --fix to auto-fix or --dry-run to preview fixes.")
        sys.exit(1)
    else:
        print("Validation passed. No issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
