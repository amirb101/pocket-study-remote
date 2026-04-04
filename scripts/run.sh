#!/usr/bin/env bash
# Build (Debug) and launch Pocket Study Remote. Menu bar only — no Dock icon.
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

echo "→ Opening app…"
open "$APP"

sleep 0.8
if pgrep -lf PocketStudyRemote >/dev/null 2>&1; then
  echo "→ Process is running. Check the menu bar (right). Crowded bar? Click « and look for the game-controller icon (tooltip: Pocket Study Remote)."
else
  echo "→ Process not detected. If macOS blocked the app: System Settings → Privacy & Security → Open Anyway, or right-click the .app → Open."
fi
echo "→ Bundle: $APP"
