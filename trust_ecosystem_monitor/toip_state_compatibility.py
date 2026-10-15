"""Inspect annual-state schema compatibility without mutating persisted state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .toip_annual_state import SCHEMA, MigrationRequiredError, migrate_to_current


def inspect(path: Path) -> dict:
    if not path.is_file():
        raise ValueError("annual state file does not exist")
    raw = json.loads(path.read_text(encoding="utf-8"))
    source_schema = raw.get("schema") if isinstance(raw, dict) else None
    try:
        state = migrate_to_current(raw)
        return {
            "compatible": True,
            "source_schema": source_schema,
            "target_schema": SCHEMA,
            "year": state.get("year"),
            "migration_required": False,
            "message": "Annual state is compatible with the current runtime schema.",
        }
    except MigrationRequiredError as exc:
        return {
            "compatible": False,
            "source_schema": source_schema,
            "target_schema": SCHEMA,
            "migration_required": True,
            "message": str(exc),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)
    result = inspect(args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["compatible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
