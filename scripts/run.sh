#!/usr/bin/env bash
# Run Pocket Study Remote (Python) from the repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "→ Creating .venv …"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "→ Installing deps …"
pip install -q -r requirements.txt

echo "→ Starting app (Ctrl+C to stop) …"
exec python -m pocket_study_remote
