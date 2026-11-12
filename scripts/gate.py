#!/usr/bin/env python3
"""
Publishing Eligibility Gate CLI.

Pure Python stdlib state machine for content publishing approval workflows:
DRAFT -> PENDING_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED
Also supports REJECTED at review/approval stage, and reopening REJECTED -> DRAFT.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VALID_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT": ["PENDING_REVIEW"],
    "PENDING_REVIEW": ["APPROVED", "REJECTED"],
    "APPROVED": ["PUBLISHED", "REJECTED"],
    "PUBLISHED": ["ARCHIVED"],
    "REJECTED": ["DRAFT"],
    "ARCHIVED": [],
}


def load_store(store_path: str) -> Dict[str, Dict[str, Any]]:
    path = Path(store_path).expanduser()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return {item["id"]: item for item in data if "id" in item}
    except Exception:
        return {}
    return {}


def save_store(store_path: str, store_data: Dict[str, Dict[str, Any]]) -> None:
    path = Path(store_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store_data, indent=2, ensure_ascii=False), encoding="utf-8")


def transition_item(
    item: Dict[str, Any],
    new_state: str,
    actor: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    current_state = item.get("state", "DRAFT")
    allowed = VALID_TRANSITIONS.get(current_state, [])
    if new_state not in allowed:
        raise ValueError(
            f"Cannot transition from {current_state} to {new_state}. Allowed: {allowed}"
        )

    now_utc = datetime.now(timezone.utc).isoformat()
    history_entry = {
        "timestamp_utc": now_utc,
        "from_state": current_state,
        "to_state": new_state,
        "actor": actor,
        "reason": reason or "",
    }
    item["state"] = new_state
    item["updated_at"] = now_utc
    if "history" not in item:
        item["history"] = []
    item["history"].append(history_entry)
    return item


def create_item(
    title: str,
    item_id: Optional[str] = None,
    actor: str = "system",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc).isoformat()
    cid = item_id or f"item-{uuid.uuid4().hex[:8]}"
    return {
        "id": cid,
        "title": title,
        "state": "DRAFT",
        "created_at": now_utc,
        "updated_at": now_utc,
        "metadata": metadata or {},
        "history": [
            {
                "timestamp_utc": now_utc,
                "from_state": "NONE",
                "to_state": "DRAFT",
                "actor": actor,
                "reason": "Initial creation",
            }
        ],
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publishing Eligibility Gate CLI (content state machine)"
    )
    parser.add_argument(
        "--store",
        default="gate_store.json",
        help="Path to JSON store file (default: gate_store.json)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create a new item in DRAFT state")
    p_create.add_argument("--title", required=True, help="Title of content item")
    p_create.add_argument("--id", help="Optional custom unique ID")
    p_create.add_argument("--actor", default="author", help="Author/actor name")

    # submit
    p_submit = subparsers.add_parser("submit", help="Submit item for review (DRAFT -> PENDING_REVIEW)")
    p_submit.add_argument("--id", required=True, help="Item ID")
    p_submit.add_argument("--actor", default="author", help="Submitting actor")

    # approve
    p_approve = subparsers.add_parser("approve", help="Approve item (PENDING_REVIEW -> APPROVED)")
    p_approve.add_argument("--id", required=True, help="Item ID")
    p_approve.add_argument("--reviewer", default="reviewer", help="Reviewer name")
    p_approve.add_argument("--notes", default="", help="Optional approval notes")

    # reject
    p_reject = subparsers.add_parser("reject", help="Reject item (PENDING_REVIEW/APPROVED -> REJECTED)")
    p_reject.add_argument("--id", required=True, help="Item ID")
    p_reject.add_argument("--reviewer", default="reviewer", help="Reviewer name")
    p_reject.add_argument("--reason", required=True, help="Rejection reason")

    # publish
    p_publish = subparsers.add_parser("publish", help="Publish approved item (APPROVED -> PUBLISHED)")
    p_publish.add_argument("--id", required=True, help="Item ID")
    p_publish.add_argument("--actor", default="publisher", help="Publisher actor")

    # archive
    p_archive = subparsers.add_parser("archive", help="Archive published item (PUBLISHED -> ARCHIVED)")
    p_archive.add_argument("--id", required=True, help="Item ID")
    p_archive.add_argument("--actor", default="admin", help="Archiving actor")

    # reopen
    p_reopen = subparsers.add_parser("reopen", help="Reopen rejected item (REJECTED -> DRAFT)")
    p_reopen.add_argument("--id", required=True, help="Item ID")
    p_reopen.add_argument("--actor", default="author", help="Actor reopening")
    p_reopen.add_argument("--reason", default="", help="Reason for reopening")

    # status
    p_status = subparsers.add_parser("status", help="Get status and details of an item")
    p_status.add_argument("--id", required=True, help="Item ID")

    # list
    p_list = subparsers.add_parser("list", help="List all items or filter by state")
    p_list.add_argument("--state", help="Filter by state (DRAFT, PENDING_REVIEW, APPROVED, etc.)")

    # history
    p_hist = subparsers.add_parser("history", help="Show full state transition history of an item")
    p_hist.add_argument("--id", required=True, help="Item ID")

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    store = load_store(args.store)

    try:
        if args.command == "create":
            item = create_item(title=args.title, item_id=args.id, actor=args.actor)
            store[item["id"]] = item
            save_store(args.store, store)
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"[CREATED] Item '{item['id']}' created in DRAFT state.")
                print(f"  Title: {item['title']}")
            return 0

        elif args.command == "submit":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            item = transition_item(store[args.id], "PENDING_REVIEW", actor=args.actor)
            save_store(args.store, store)
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"[SUBMITTED] Item '{args.id}' moved to PENDING_REVIEW by {args.actor}.")
            return 0

        elif args.command == "approve":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            item = transition_item(store[args.id], "APPROVED", actor=args.reviewer, reason=args.notes)
            save_store(args.store, store)
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"[APPROVED] Item '{args.id}' approved by {args.reviewer}.")
            return 0

        elif args.command == "reject":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            item = transition_item(store[args.id], "REJECTED", actor=args.reviewer, reason=args.reason)
            save_store(args.store, store)
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"[REJECTED] Item '{args.id}' rejected by {args.reviewer}. Reason: {args.reason}")
            return 0

        elif args.command == "publish":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            item = transition_item(store[args.id], "PUBLISHED", actor=args.actor)
            save_store(args.store, store)
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"[PUBLISHED] Item '{args.id}' published by {args.actor}.")
            return 0

        elif args.command == "archive":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            item = transition_item(store[args.id], "ARCHIVED", actor=args.actor)
            save_store(args.store, store)
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"[ARCHIVED] Item '{args.id}' archived by {args.actor}.")
            return 0

        elif args.command == "reopen":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            item = transition_item(store[args.id], "DRAFT", actor=args.actor, reason=args.reason)
            save_store(args.store, store)
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"[REOPENED] Item '{args.id}' reopened to DRAFT state by {args.actor}.")
            return 0

        elif args.command == "status":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            item = store[args.id]
            if args.json:
                print(json.dumps(item, indent=2))
            else:
                print(f"Item ID:     {item['id']}")
                print(f"Title:       {item['title']}")
                print(f"State:       {item['state']}")
                print(f"Created:     {item['created_at']}")
                print(f"Updated:     {item['updated_at']}")
                print(f"Transitions: {len(item.get('history', []))}")
            return 0

        elif args.command == "list":
            items = list(store.values())
            if args.state:
                items = [it for it in items if it.get("state") == args.state.upper()]
            if args.json:
                print(json.dumps(items, indent=2))
            else:
                print(f"Total Items: {len(items)}" + (f" (Filtered by state: {args.state})" if args.state else ""))
                for it in items:
                    print(f" - [{it['state']}] {it['id']} - {it['title']}")
            return 0

        elif args.command == "history":
            if args.id not in store:
                raise KeyError(f"Item not found: {args.id}")
            hist = store[args.id].get("history", [])
            if args.json:
                print(json.dumps(hist, indent=2))
            else:
                print(f"History for item '{args.id}':")
                for h in hist:
                    r_str = f" (Reason: {h['reason']})" if h.get("reason") else ""
                    print(f" - [{h['timestamp_utc']}] {h['from_state']} -> {h['to_state']} by {h['actor']}{r_str}")
            return 0

    except Exception as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

