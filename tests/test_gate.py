"""
Unit and functional tests for publishing-eligibility-gate.
"""

import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.gate import (
    create_item,
    transition_item,
    load_store,
    save_store,
    main,
)


def test_create_item():
    item = create_item("Test Post", item_id="post-100", actor="alice")
    assert item["id"] == "post-100"
    assert item["title"] == "Test Post"
    assert item["state"] == "DRAFT"
    assert len(item["history"]) == 1
    assert item["history"][0]["to_state"] == "DRAFT"
    assert item["history"][0]["actor"] == "alice"


def test_valid_transitions():
    item = create_item("Lifecycle Post", item_id="post-200")
    assert item["state"] == "DRAFT"

    # DRAFT -> PENDING_REVIEW
    transition_item(item, "PENDING_REVIEW", actor="alice")
    assert item["state"] == "PENDING_REVIEW"

    # PENDING_REVIEW -> APPROVED
    transition_item(item, "APPROVED", actor="bob", reason="Looks solid")
    assert item["state"] == "APPROVED"

    # APPROVED -> PUBLISHED
    transition_item(item, "PUBLISHED", actor="bot")
    assert item["state"] == "PUBLISHED"

    # PUBLISHED -> ARCHIVED
    transition_item(item, "ARCHIVED", actor="admin")
    assert item["state"] == "ARCHIVED"

    assert len(item["history"]) == 5


def test_invalid_transition():
    item = create_item("Bad Transition Post", item_id="post-300")
    # Cannot jump DRAFT directly to PUBLISHED or APPROVED
    with pytest.raises(ValueError) as excinfo:
        transition_item(item, "PUBLISHED", actor="alice")
    assert "Cannot transition from DRAFT to PUBLISHED" in str(excinfo.value)


def test_reject_and_reopen():
    item = create_item("Rejectable Post", item_id="post-400")
    transition_item(item, "PENDING_REVIEW", actor="alice")
    transition_item(item, "REJECTED", actor="editor", reason="Needs more data")
    assert item["state"] == "REJECTED"

    # Reopen back to DRAFT
    transition_item(item, "DRAFT", actor="alice", reason="Added extra data")
    assert item["state"] == "DRAFT"


def test_history_recorded():
    item = create_item("Audited Post", item_id="post-500")
    transition_item(item, "PENDING_REVIEW", actor="reporter")
    transition_item(item, "APPROVED", actor="lead_editor", reason="Fact-checked")

    hist = item["history"]
    assert len(hist) == 3
    assert hist[1]["from_state"] == "DRAFT"
    assert hist[1]["to_state"] == "PENDING_REVIEW"
    assert hist[2]["from_state"] == "PENDING_REVIEW"
    assert hist[2]["to_state"] == "APPROVED"
    assert hist[2]["reason"] == "Fact-checked"


def test_cli_end_to_end(tmp_path):
    store_file = str(tmp_path / "test_store.json")

    # CLI create
    rc = main(["--store", store_file, "create", "--title", "CLI Post", "--id", "cli-1"])
    assert rc == 0

    # CLI submit
    rc = main(["--store", store_file, "submit", "--id", "cli-1", "--actor", "dev"])
    assert rc == 0

    # CLI approve
    rc = main(["--store", store_file, "approve", "--id", "cli-1", "--reviewer", "lead"])
    assert rc == 0

    # CLI list
    rc = main(["--store", store_file, "--json", "list", "--state", "APPROVED"])
    assert rc == 0

    store = load_store(store_file)
    assert "cli-1" in store
    assert store["cli-1"]["state"] == "APPROVED"

