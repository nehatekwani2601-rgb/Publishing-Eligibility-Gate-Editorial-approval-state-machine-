# Publishing Eligibility Gate

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![stdlib only](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen.svg)](scripts/gate.py)
[![Tests](https://img.shields.io/badge/tests-pytest-orange.svg)](tests/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/RadheWankhade01/publishing-eligibility-gate/pulls)

> **A pure Python stdlib state machine CLI for content approval workflows.**
> Track content through DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ARCHIVED with full history, JSON persistence, and CI/CD integration.

**Developer:** [Neha Tekwani](https://github.com/nehatekwani2601-rgb) / [@nehatekwani2601-rgb](https://github.com/nehatekwani2601-rgb)
**Developer:** [Radhe Wankhade](https://x.com/RadheWankhade01) / [@RadheWankhade01](https://x.com/RadheWankhade01)
---

## Table of Contents

- [Overview](#overview)
- [State Machine](#state-machine)
- [Installation](#installation)
- [CLI Usage Examples](#cli-usage-examples)
- [CLI Reference](#cli-reference)
- [JSON State Store Format](#json-state-store-format)
- [Use Cases](#use-cases)
- [Running Tests](#running-tests)
- [CI/CD Integration](#cicd-integration)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The **Publishing Eligibility Gate** enforces a structured content approval lifecycle. Whether you're managing blog posts, marketing copy, API documentation, or social media content — this tool ensures nothing goes live without passing through the right checkpoints.

**Key features:**
- 🔁 Full state machine with 7 valid transitions
- 📝 Complete history log for every item (who did what, when, why)
- 💾 JSON file persistence — commit your store to git for team visibility
- 🔒 Invalid transitions are blocked with clear error messages
- 🚀 Zero dependencies — pure Python 3.8+ stdlib
- 🤖 CI/CD ready with `--json` output and example gate-check script

---

## State Machine

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
              ┌──────────┐    submit    ┌────────────────┐│
              │  DRAFT   │─────────────▶│ PENDING_REVIEW ││
              └──────────┘              └────────────────┘│
                    ▲                    │         │       │
                    │                   │approve  │reject  │
                 reopen                 ▼         ▼       │
                    │            ┌──────────┐ ┌──────────┐│
                    │            │ APPROVED │ │          ││
                    │            └──────────┘ │          ││
                    │             │    │      │ REJECTED │││
                    │          publish │reject│          ││
                    │             ▼    └─────▶│          ││
                    │       ┌───────────┐     └──────────┘│
                    └───────│           │                  │
                            │ PUBLISHED │                  │
                            └───────────┘                  │
                                  │                        │
                                archive                    │
                                  ▼                        │
                            ┌──────────┐                   │
                            │ ARCHIVED │                   │
                            └──────────┘                   │
                                                           │
                    ─────────────────────────────────────── ┘
```

### Transition Table

| From State       | Command   | To State         |
|------------------|-----------|------------------|
| `DRAFT`          | `submit`  | `PENDING_REVIEW` |
| `PENDING_REVIEW` | `approve` | `APPROVED`       |
| `PENDING_REVIEW` | `reject`  | `REJECTED`       |
| `APPROVED`       | `publish` | `PUBLISHED`      |
| `APPROVED`       | `reject`  | `REJECTED`       |
| `PUBLISHED`      | `archive` | `ARCHIVED`       |
| `REJECTED`       | `reopen`  | `DRAFT`          |

Any other transition is **INVALID** and will exit with code 1.

---

## Installation

No installation required — pure Python stdlib.

```bash
git clone https://github.com/RadheWankhade01/publishing-eligibility-gate.git
cd publishing-eligibility-gate
python scripts/gate.py --help
```

For running tests:

```bash
pip install pytest
pytest -v
```

---

## CLI Usage Examples

### Example 1: Create a new content item

```bash
$ python scripts/gate.py create --title "Q4 Product Launch Blog Post"

✓ Created item
  ID:    a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Title: Q4 Product Launch Blog Post
  State: DRAFT
```

### Example 2: Submit for review

```bash
$ python scripts/gate.py submit --id a1b2c3d4-e5f6-7890-abcd-ef1234567890

✓ Transition: DRAFT → PENDING_REVIEW
  ID:    a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Title: Q4 Product Launch Blog Post
  State: PENDING_REVIEW
```

### Example 3: Approve and publish

```bash
$ python scripts/gate.py approve --id a1b2c3d4-e5f6-7890-abcd-ef1234567890 --reviewer "alice@company.com"

✓ Transition: PENDING_REVIEW → APPROVED
  ID:       a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Reviewer: alice@company.com
  State:    APPROVED

$ python scripts/gate.py publish --id a1b2c3d4-e5f6-7890-abcd-ef1234567890

✓ Transition: APPROVED → PUBLISHED
  ID:    a1b2c3d4-e5f6-7890-abcd-ef1234567890
  State: PUBLISHED
```

### Example 4: Reject and reopen for revision

```bash
$ python scripts/gate.py reject --id a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
    --reviewer "bob@company.com" --reason "Needs more data to support claims"

✓ Transition: PENDING_REVIEW → REJECTED
  ID:     a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Reason: Needs more data to support claims
  State:  REJECTED

$ python scripts/gate.py reopen --id a1b2c3d4-e5f6-7890-abcd-ef1234567890

✓ Transition: REJECTED → DRAFT
  ID:    a1b2c3d4-e5f6-7890-abcd-ef1234567890
  State: DRAFT
```

### Example 5: List all items and filter by state

```bash
$ python scripts/gate.py list

ID                                   TITLE                          STATE
------------------------------------+------------------------------+----------------
a1b2c3d4-e5f6-7890-abcd-ef1234567890 Q4 Product Launch Blog Post   PENDING_REVIEW
b2c3d4e5-f6a7-8901-bcde-f12345678901 API Documentation Update      DRAFT
c3d4e5f6-a7b8-9012-cdef-123456789012 Social Media Campaign         PUBLISHED

$ python scripts/gate.py list --state PENDING_REVIEW

ID                                   TITLE                          STATE
------------------------------------+------------------------------+----------------
a1b2c3d4-e5f6-7890-abcd-ef1234567890 Q4 Product Launch Blog Post   PENDING_REVIEW
```

### Example 6: Check full history with JSON output

```bash
$ python scripts/gate.py status --id a1b2c3d4-e5f6-7890-abcd-ef1234567890 --json

{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Q4 Product Launch Blog Post",
  "state": "PENDING_REVIEW",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "history": [
    {
      "timestamp_utc": "2024-01-15T10:00:00Z",
      "from_state": null,
      "to_state": "DRAFT",
      "actor": "system",
      "reason": null
    },
    {
      "timestamp_utc": "2024-01-15T10:30:00Z",
      "from_state": "DRAFT",
      "to_state": "PENDING_REVIEW",
      "actor": "system",
      "reason": null
    }
  ]
}
```

### Example 7: Invalid transition (blocked)

```bash
$ python scripts/gate.py approve --id a1b2c3d4-e5f6-7890-abcd-ef1234567890

Error: Cannot transition from DRAFT to APPROVED
$ echo $?
1
```

---

## CLI Reference

```
python scripts/gate.py <command> [options]
```

### Global Options

| Option           | Default              | Description                                |
|------------------|----------------------|--------------------------------------------|
| `--store FILE`   | `./gate_store.json`  | Path to JSON persistence file              |
| `--json`         | —                    | Output structured JSON instead of text     |

### Commands

| Command   | Required Args            | Optional Args                      | Description                             |
|-----------|--------------------------|------------------------------------|-----------------------------------------|
| `create`  | `--title TITLE`          | `--store`                          | Create new item (auto UUID), state=DRAFT|
| `submit`  | `--id ID`                | `--store`                          | DRAFT → PENDING_REVIEW                  |
| `approve` | `--id ID`                | `--reviewer REVIEWER`, `--store`   | PENDING_REVIEW → APPROVED               |
| `reject`  | `--id ID`                | `--reviewer REVIEWER`, `--reason REASON`, `--store` | → REJECTED         |
| `publish` | `--id ID`                | `--store`                          | APPROVED → PUBLISHED                    |
| `archive` | `--id ID`                | `--store`                          | PUBLISHED → ARCHIVED                    |
| `reopen`  | `--id ID`                | `--store`                          | REJECTED → DRAFT                        |
| `status`  | `--id ID`                | `--json`, `--store`                | Show item details + full history        |
| `list`    | —                        | `--state STATE`, `--json`, `--store` | List all items                        |
| `history` | `--id ID`                | `--json`, `--store`                | Show transition history only            |

---

## JSON State Store Format

The store file is a plain JSON document. It's safe to commit to version control.

```json
{
  "items": {
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Q4 Product Launch Blog Post",
      "state": "PUBLISHED",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T12:00:00Z",
      "history": [
        {
          "timestamp_utc": "2024-01-15T10:00:00Z",
          "from_state": null,
          "to_state": "DRAFT",
          "actor": "system",
          "reason": null
        },
        {
          "timestamp_utc": "2024-01-15T10:30:00Z",
          "from_state": "DRAFT",
          "to_state": "PENDING_REVIEW",
          "actor": "system",
          "reason": null
        },
        {
          "timestamp_utc": "2024-01-15T11:00:00Z",
          "from_state": "PENDING_REVIEW",
          "to_state": "APPROVED",
          "actor": "alice@company.com",
          "reason": null
        },
        {
          "timestamp_utc": "2024-01-15T12:00:00Z",
          "from_state": "APPROVED",
          "to_state": "PUBLISHED",
          "actor": "system",
          "reason": null
        }
      ]
    }
  }
}
```

---

## Use Cases

| Use Case                        | How to Use                                                                 |
|---------------------------------|----------------------------------------------------------------------------|
| **Blog editorial workflow**     | Authors create → editors approve → admins publish                          |
| **API documentation review**    | Devs draft → tech writers review → DevRel publish                          |
| **Social media content**        | Content team creates → brand reviews → scheduler publishes                 |
| **Marketing campaign copy**     | Copywriter drafts → marketing approves → deploys                           |
| **Legal document clearance**    | Author drafts → legal reviews → compliance approves → publishes            |
| **CI/CD release gate**          | Use `ci_gate_check.py` — block deploy if any item not APPROVED/PUBLISHED   |
| **Multi-stage content pipeline**| Automate transitions in GitHub Actions with `--json` output parsing        |
| **Audit compliance**            | Full history log provides who approved what, when, and why                 |

---

## Running Tests

```bash
pip install pytest
pytest -v
```

Expected output:

```
tests/test_gate.py::test_create_item PASSED
tests/test_gate.py::test_valid_transitions PASSED
tests/test_gate.py::test_invalid_transition PASSED
tests/test_gate.py::test_reject_and_reopen PASSED
tests/test_gate.py::test_history_recorded PASSED
tests/test_gate.py::test_list_filter PASSED

6 passed in 0.XXs
```

---

## CI/CD Integration

Use the included `examples/ci_gate_check.py` to block deployment if any tracked content item is not in an approved/published state:

```yaml
# GitHub Actions example
- name: Check publishing gate
  run: python examples/ci_gate_check.py --store ./gate_store.json
```

Or inline:

```bash
python examples/ci_gate_check.py --store ./gate_store.json || exit 1
```

---

## 🔗 Connected Skills Ecosystem

This tool is part of a modular **Open-Source Content & Intelligence Pipeline**. Each tool works 100% standalone, or combines seamlessly with the others:

```
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│     Safe RSS News Ingestor           │       │       Trading Chart Exporter         │
│  (SSRF-safe news & feeds)            │       │   (High-res headless chart capture)  │
└──────────────────┬───────────────────┘       └──────────────────┬───────────────────┘
                   │                                              │
                   ▼                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          QC Tweet & Thread Composer                                 │
│         (Deterministic numeric grounding & anti-hallucination verification)         │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Publishing Eligibility Gate                                 │
│            (DRAFT ➔ PENDING_REVIEW ➔ APPROVED ➔ PUBLISHED state machine)            │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            Zero-Cost X Publisher                                    │
│             (Web Intent + OS Clipboard PNG Ctrl+V @ $0 API cost)                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                           ▲
                                           │ Orchestrated by
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    FastAPI + Celery + Docker Starter                                │
│             (Production async backend, Redis task queue & PostgreSQL)               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

| Pipeline Stage | Repository | Purpose |
|---|---|---|
| **1. News Ingestion** | [📰 safe-rss-news-ingestor](https://github.com/peacecoder123/A-production-safe-RSS-Atom-news-aggregator) | Hardened RSS/Atom aggregator that prevents SSRF attacks and strips junk HTML |
| **2. Chart Visuals** | [📊 trading-chart-exporter](https://github.com/peacecoder123/Trading-chart-exporter-Trading-view-alternative-Skill-) | Headless Playwright exporter for TradingView charts & financial visuals |
| **3. AI Content QC** | [✍️ qc-tweet-composer](https://github.com/peacecoder123/Quality-Control-gate-for-AI-drafted-tweets-threads-Ai-Skill-) | Fact-checks AI post drafts against sources, catches fake metrics & splits threads |
| **4. Editorial Gate** | [🚦 publishing-eligibility-gate](https://github.com/peacecoder123/publishing-eligibility-gate) *(This repo)* | Content review state machine with audit history preventing unapproved releases |
| **5. $0 Distribution** | [🚀 zero-cost-x-publisher](https://github.com/peacecoder123/zero-cost-X-Twitter-publisher) | Publishes text + image to X at $0 cost via web intent + clipboard Ctrl+V |
| **6. Backend Engine** | [⚡ fastapi-celery-docker-starter](https://github.com/peacecoder123/Production-ready-FastAPI-Celery-Redis-PostgreSQL-Docker-starter) | Production async backend stack with Celery workers, Redis, and PostgreSQL |

---

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

MIT © [Neha Tekwani](https://github.com/nehatekwani2601-rgb) — see [LICENSE](LICENSE) for details.
MIT © [Radhe Wankhade](https://x.com/RadheWankhade01) — see [LICENSE](LICENSE) for details.
