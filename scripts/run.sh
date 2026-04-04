#!/usr/bin/env bash
# Build (Debug) and launch Pocket Study Remote. Menu bar only — no Dock icon.
# Safe to run from iTerm: when this script exits, the app keeps running (LaunchServices).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DERIVED="${ROOT}/build/RunDerived"
APP="${DERIVED}/Build/Products/Debug/PocketStudyRemote.app"

echo "→ Building…"
xcodebuild \
  -project PocketStudyRemote.xcodeproj \
  -scheme PocketStudyRemote \
  -configuration Debug \
  -derivedDataPath "$DERIVED" \
  CODE_SIGNING_ALLOWED=NO \
  build

echo "→ Opening app (this terminal can close — the app is separate)…"
open "$APP"

echo "→ Waiting for process…"
sleep 2
if pgrep -lf PocketStudyRemote >/dev/null 2>&1; then
  echo "→ Still running. Menu bar (top right): game-controller icon or “PSR”; full bar? Click « overflow. Tooltip: Pocket Study Remote."
else
  echo "→ Process disappeared — likely a crash. Recent logs (if any):"
  log show --style compact --predicate 'process == "PocketStudyRemote" OR eventMessage CONTAINS[c] "PocketStudyRemote"' --last 2m 2>/dev/null | tail -30 || true
  echo "→ Also check: Console.app → Crash Reports, filter PocketStudyRemote."
fi
echo "→ App: $APP"

if [[ "${KEEP_TERMINAL_OPEN:-}" == 1 ]]; then
  read -rp "Press Enter to close this window…"
fi
