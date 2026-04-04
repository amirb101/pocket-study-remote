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

echo "→ Quitting any previous instance (stale process can fool pgrep)…"
killall PocketStudyRemote 2>/dev/null || true
sleep 0.3

echo "→ Opening app (this terminal can close — the app is separate)…"
open "$APP"

echo "→ Waiting for process (up to ~5s)…"
running=""
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if pgrep -x PocketStudyRemote >/dev/null 2>&1; then
    running=1
    break
  fi
  sleep 0.5
done

if [[ -n "$running" ]]; then
  echo "→ Still running as PID(s): $(pgrep -x PocketStudyRemote | tr '\n' ' ')"
  echo "→ UI: menu bar top-right — game-controller icon or “PSR”; crowded bar? Click « overflow. Tooltip: Pocket Study Remote."
else
  echo "→ No process named PocketStudyRemote — it may have crashed on launch."
  echo "→ Quick check: ps aux | grep -i PocketStudy"
  shopt -s nullglob
  crashes=(~/Library/Logs/DiagnosticReports/PocketStudyRemote*.ips)
  if ((${#crashes[@]})); then
    echo "→ Newest crash report(s):"
    ls -lt "${crashes[@]}" 2>/dev/null | head -3
  else
    echo "→ No *.ips crash reports matching PocketStudyRemote in ~/Library/Logs/DiagnosticReports/"
  fi
  echo "→ Open Console.app → Crash Reports, or run the app from Xcode (⌘R) to see the debugger."
fi
echo "→ App: $APP"

if [[ "${KEEP_TERMINAL_OPEN:-}" == 1 ]]; then
  read -rp "Press Enter to close this window…"
fi
