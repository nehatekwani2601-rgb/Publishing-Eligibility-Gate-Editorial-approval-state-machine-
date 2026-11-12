#!/usr/bin/env python3
"""
ci_gate_check.py — Example CI/CD gate check script.

Ensures no pending, unapproved, or rejected items are scheduled for release.
Exits with code 0 if all items are APPROVED or PUBLISHED, or code 1 if unapproved items exist.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="CI gate check for approved content")
    parser.add_argument("--store", default="gate_store.json", help="Path to gate store JSON")
    args = parser.parse_args()

    store_file = Path(args.store)
    if not store_file.exists():
        print(f"Error: Store file {store_file} does not exist.", file=sys.stderr)
        return 1

    data = json.loads(store_file.read_text(encoding="utf-8"))
    items = list(data.values()) if isinstance(data, dict) else data

    blocking_items = [
        item for item in items
        if item.get("state") not in ("APPROVED", "PUBLISHED", "ARCHIVED")
    ]

    if blocking_items:
        print(f"FAILED: {len(blocking_items)} item(s) are not yet approved for release:")
        for it in blocking_items:
            print(f" - [{it.get('state')}] {it.get('id')}: {it.get('title')}")
        return 1

    print(f"PASSED: All {len(items)} items in {args.store} are eligible for release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

