#!/usr/bin/env bash
# install_scheduler.sh
# Installs a Mac launchd agent that runs `make fetch` at 7:50 AM every day,
# 10 minutes before the Cowork task fires at 8:00 AM.
#
# Run once from inside the mbs-yellowdig-cowork folder:
#   chmod +x install_scheduler.sh && ./install_scheduler.sh

set -euo pipefail

LABEL="au.mulla.yellowdig-fetch"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
WORKDIR="$(cd "$(dirname "$0")" && pwd)"
LOGFILE="$WORKDIR/fetch.log"
MAKEPATH="$(command -v make)"

echo "=== Yellowdig Fetch Scheduler ==="
echo ""
echo "Workspace : $WORKDIR"
echo "Log file  : $LOGFILE"
echo "make      : $MAKEPATH"
echo ""

# ── 1. Ensure the venv is set up ─────────────────────────────────────────────
if [ ! -f "$WORKDIR/.venv/bin/python" ]; then
  echo "Setting up Python virtual environment …"
  make -C "$WORKDIR" setup
  echo ""
fi

# ── 2. Verify fetch works right now ──────────────────────────────────────────
echo "Testing fetch (this will hit the Yellowdig API) …"
if make -C "$WORKDIR" fetch; then
  echo "  ✓ Fetch succeeded — posts.json updated."
else
  echo ""
  echo "  ✗ Fetch failed. Check your config.json (api_key, network, community)"
  echo "    and make sure you're on a network where Yellowdig is accessible."
  echo "    Fix the issue and re-run this script."
  exit 1
fi
echo ""

# ── 3. Write the launchd plist ────────────────────────────────────────────────
echo "Writing launchd plist to $PLIST …"
cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>

  <key>ProgramArguments</key>
  <array>
    <string>${MAKEPATH}</string>
    <string>-C</string>
    <string>${WORKDIR}</string>
    <string>fetch</string>
  </array>

  <!-- Run at 7:50 AM every day — 10 min before the Cowork task -->
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>7</integer>
    <key>Minute</key>
    <integer>50</integer>
  </dict>

  <key>StandardOutPath</key>
  <string>${LOGFILE}</string>
  <key>StandardErrorPath</key>
  <string>${LOGFILE}</string>

  <!-- Run missed jobs when the Mac wakes (e.g. lid was closed at 7:50) -->
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLIST_EOF

# ── 4. Unload any existing version, then load the new one ────────────────────
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"

echo "  ✓ Agent loaded."
echo ""
echo "=== Done! ==="
echo ""
echo "The fetch will now run automatically at 7:50 AM every day."
echo "Output is logged to: $LOGFILE"
echo ""
echo "Useful commands:"
echo "  Run fetch manually now  : make fetch"
echo "  Check the log           : cat \"$LOGFILE\""
echo "  Uninstall               : launchctl unload \"$PLIST\" && rm \"$PLIST\""
echo ""
