---
name: publishing-eligibility-gate
description: >
  A pure Python stdlib state machine CLI for content approval workflows.
  Manages items through DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ARCHIVED
  states with full history tracking, JSON persistence, and CI/CD integration support.
author: "Radhe Wankhade (@RadheWankhade01)"
x_profile: "https://x.com/RadheWankhade01"
version: "1.0.0"
tags:
  - publishing
  - content-approval
  - state-machine
  - workflow
  - cli
  - stdlib
---

# Publishing Eligibility Gate — Agent Skill Instructions

## What This Skill Does

This skill provides a **content publishing approval gate** — a state machine that tracks content items through a structured approval workflow. Use it to enforce editorial review, QA sign-off, or any multi-stage approval process before content goes live.

## State Machine

```
DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ARCHIVED
                       ↘ REJECTED ↗
                         REJECTED → DRAFT (reopen)
```

**States:**
- `DRAFT` — Initial state, item is being worked on
- `PENDING_REVIEW` — Submitted for review, awaiting decision
- `APPROVED` — Reviewed and approved, ready to publish
- `PUBLISHED` — Live/published
- `ARCHIVED` — Retired from active use
- `REJECTED` — Declined at review stage (can be reopened to DRAFT)

## Core CLI (`scripts/gate.py`)

All commands use pure Python stdlib — no pip installs needed.

```bash
python scripts/gate.py <command> [options]
```

### Commands

| Command   | Description                                 |
|-----------|---------------------------------------------|
| `create`  | Create a new item (auto-assigns UUID)       |
| `submit`  | Submit DRAFT → PENDING_REVIEW               |
| `approve` | Approve PENDING_REVIEW → APPROVED           |
| `reject`  | Reject to REJECTED (from PENDING_REVIEW or APPROVED) |
| `publish` | Publish APPROVED → PUBLISHED                |
| `archive` | Archive PUBLISHED → ARCHIVED                |
| `reopen`  | Reopen REJECTED → DRAFT                     |
| `status`  | Show item details and full history          |
| `list`    | List all items (filter with `--state`)      |
| `history` | Show transition history for an item         |

### Key Options

- `--store FILE` — Path to JSON store file (default: `./gate_store.json`)
- `--id ID` — Item ID for all commands except `create`
- `--title TITLE` — Title for `create`
- `--reason REASON` — Reason text for `reject`
- `--reviewer REVIEWER` — Reviewer name for `approve`/`reject`
- `--state STATE` — Filter for `list` command
- `--json` — Output structured JSON instead of human-readable text

## Agent Usage Patterns

### Pattern 1: Create and Submit for Review

```bash
# Create a new content item
ID=$(python scripts/gate.py create --title "My Blog Post" --json | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Submit for review
python scripts/gate.py submit --id $ID
```

### Pattern 2: Review and Approve

```bash
# List items pending review
python scripts/gate.py list --state PENDING_REVIEW

# Approve an item
python scripts/gate.py approve --id <ID> --reviewer "editor@example.com"

# Publish it
python scripts/gate.py publish --id <ID>
```

### Pattern 3: CI/CD Gate Check

```bash
# Exit non-zero if any item is not in APPROVED or PUBLISHED state
python examples/ci_gate_check.py --store ./gate_store.json
```

### Pattern 4: Full Workflow Automation

```bash
# Run the sample workflow script to see all transitions
bash examples/sample_workflow.sh
```

## JSON Store Format

The store is a plain JSON file at `--store` path:

```json
{
  "items": {
    "<uuid>": {
      "id": "<uuid>",
      "title": "...",
      "state": "PUBLISHED",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T11:30:00Z",
      "history": [
        {
          "timestamp_utc": "2024-01-15T10:00:00Z",
          "from_state": null,
          "to_state": "DRAFT",
          "actor": "system",
          "reason": null
        }
      ]
    }
  }
}
```

## Integration Notes

- **No dependencies** — pure Python 3.8+ stdlib only
- **Idempotent store** — JSON file is safe to commit to version control
- **Exit codes** — 0 for success, 1 for invalid transitions or errors
- **CI-friendly** — Use `--json` for machine-readable output in pipelines
- **Thread safety** — Not designed for concurrent writes; use a single process or add file locking for concurrent use

## Common Agent Tasks

1. **Enforce review before publish**: Check `--state` before allowing deployment scripts to continue
2. **Audit trail**: Use `history` command or `--json` to log who approved what and when
3. **Batch status check**: Use `list --state PENDING_REVIEW` to find items awaiting action
4. **Reopen rejected items**: Use `reopen` to send back to DRAFT for revision
