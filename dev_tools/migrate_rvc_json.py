"""
Migrate legacy rvc.json (messages array) to new pgns dict format for rvc2api backend.

Usage:
    poetry run python dev_tools/migrate_rvc_json.py [--dry-run] [--file <path>]

- Reads backend/integrations/rvc/config/rvc.json by default
- Writes the new format to the same file (backup as rvc.json.bak)
- Skips empty/malformed entries
- Use --dry-run to print output instead of writing
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

DEFAULT_SRC = Path(__file__).parent.parent / "backend/integrations/rvc/config/rvc.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def migrate_rvc_json(path: Path, dry_run: bool = False) -> None:
    """Migrate legacy rvc.json to new pgns dict format, with backup and error handling."""
    if not path.exists():
        logging.error(f"File not found: {path}")
        return
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    messages = data.get("messages", [])
    pgns: dict[str, Any] = {}
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        msg_id = msg.get("id")
        if msg_id is None:
            continue
        key = str(msg_id)
        pgns[key] = msg
    if dry_run:
        print(json.dumps({"pgns": pgns}, indent=2, ensure_ascii=False))
        logging.info("Dry run: no changes written.")
        return
    backup = path.with_suffix(".bak")
    try:
        path.rename(backup)
        logging.info(f"Backup saved as {backup}.")
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return
    with path.open("w", encoding="utf-8") as f:
        json.dump({"pgns": pgns}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    logging.info(f"Migrated {len(pgns)} messages to 'pgns' format. New file written to {path}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate legacy rvc.json to new pgns format.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print output instead of writing file"
    )
    parser.add_argument("--file", type=Path, default=DEFAULT_SRC, help="Path to rvc.json file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    migrate_rvc_json(args.file, dry_run=args.dry_run)
