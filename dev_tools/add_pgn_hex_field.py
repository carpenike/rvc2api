"""
Script to add a 'pgn' hex string field to each PGN entry in rvc.json.
- Computes the 18-bit PGN from the 'id' field (id >> 8 & 0x3FFFF)
- Adds 'pgn': '0xXXXXX' (uppercase hex)
- Overwrites the original file after making a backup

Usage:
    poetry run python dev_tools/add_pgn_hex_field.py [--dry-run] [--file <path>]

Options:
    --dry-run   Print changes but do not write to file
    --file      Path to rvc.json (default: backend/integrations/rvc/config/rvc.json)
"""
import argparse
import json
import logging
import shutil
from pathlib import Path

DEFAULT_RVC_JSON_PATH = Path("backend/integrations/rvc/config/rvc.json")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def add_pgn_fields(rvc_json_path: Path, dry_run: bool = False) -> None:
    """Add 'pgn' hex string field to each PGN entry in the given rvc.json file."""
    if not rvc_json_path.exists():
        logging.error(f"File not found: {rvc_json_path}")
        return
    backup_path = rvc_json_path.with_suffix(".bak")
    # Backup original file
    shutil.copy2(rvc_json_path, backup_path)
    with rvc_json_path.open("r", encoding="utf-8") as f:
        data: dict[str, dict] = json.load(f)
    pgns = data.get("pgns", {})
    updated = False
    for key, entry in pgns.items():
        pgn_id = entry.get("id")
        if pgn_id is None:
            logging.warning(f"Missing 'id' for PGN key: {key}")
            continue
        try:
            pgn_val = (int(pgn_id) >> 8) & 0x3FFFF
            hex_str = f"0x{pgn_val:X}"
            if entry.get("pgn") != hex_str:
                entry["pgn"] = hex_str
                updated = True
        except Exception as e:
            logging.error(f"Error processing PGN key {key}: {e}")
    if dry_run:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        logging.info("Dry run: no changes written.")
    else:
        with rvc_json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if updated:
            logging.info(
                f"Updated {rvc_json_path} with 'pgn' fields. Backup saved as {backup_path}."
            )
        else:
            logging.info("No changes made (all PGNs already had correct 'pgn' fields).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add 'pgn' hex field to rvc.json PGNs.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print changes but do not write to file"
    )
    parser.add_argument(
        "--file", type=Path, default=DEFAULT_RVC_JSON_PATH, help="Path to rvc.json file"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    add_pgn_fields(args.file, dry_run=args.dry_run)
