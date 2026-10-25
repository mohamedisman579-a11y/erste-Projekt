#!/usr/bin/env bash
# Installiert die Hilfsprogramme für den Skill (yt-dlp, youtube-transcript-api).
set -euo pipefail
cd "$(dirname "$0")"
chmod +x scripts/video_ansehen.py
PY=$(command -v python3 || command -v python)
for pkg in yt-dlp youtube-transcript-api; do
  "$PY" -m pip install --user -q -U "$pkg" 2>/dev/null \
    || "$PY" -m pip install --user -q -U --break-system-packages "$pkg" \
    || echo "Hinweis: $pkg konnte nicht installiert werden (z. B. mit 'brew install yt-dlp' versuchen)."
done
echo "Fertig! Starte Claude neu und schick einen YouTube-Link mit: \"Schau dir dieses Video an\"."
