#!/usr/bin/env bash
# Sample end-to-end publishing workflow demo
set -e

STORE="./gate_store.json"

echo "=== 1. Create content draft ==="
python scripts/gate.py --store "$STORE" create --title "Q3 Market Overview Thread" --id "post-001"

echo -e "\n=== 2. Submit for editorial review ==="
python scripts/gate.py --store "$STORE" submit --id "post-001" --actor "analyst"

echo -e "\n=== 3. Editor approves the draft ==="
python scripts/gate.py --store "$STORE" approve --id "post-001" --reviewer "editor" --notes "Numbers verified against 10-Q filing"

echo -e "\n=== 4. Check status before publishing ==="
python scripts/gate.py --store "$STORE" status --id "post-001"

echo -e "\n=== 5. Publish to social media ==="
python scripts/gate.py --store "$STORE" publish --id "post-001" --actor "publisher_bot"

echo -e "\n=== 6. View full audit trail ==="
python scripts/gate.py --store "$STORE" history --id "post-001"

