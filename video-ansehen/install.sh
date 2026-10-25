#!/usr/bin/env bash
# Installiert yt-dlp, das der Skill zum Holen der Transkripte braucht.
set -euo pipefail

cd "$(dirname "$0")"
chmod +x scripts/transkript.sh

if command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp ist schon installiert: $(yt-dlp --version)"
elif command -v brew >/dev/null 2>&1; then
  brew install yt-dlp
elif command -v pipx >/dev/null 2>&1; then
  pipx install yt-dlp
else
  python3 -m pip install --user -U yt-dlp || python3 -m pip install --user -U --break-system-packages yt-dlp
fi

echo "Fertig! Starte Claude neu und schick einen YouTube-Link mit: \"Schau dir dieses Video an\"."
