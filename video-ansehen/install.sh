#!/usr/bin/env bash
# Installiert alles für den Skill "video-ansehen" auf dem Mac (und Linux).
# Danach: Skill nach ~/.claude/skills/video-ansehen kopieren (macht dieses Skript automatisch).
set -euo pipefail
HIER="$(cd "$(dirname "$0")" && pwd)"

if [ "$(uname)" = "Darwin" ]; then
  if ! command -v brew >/dev/null; then
    echo "→ Installiere Homebrew …"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Homebrew in den PATH aufnehmen (Apple Silicon bzw. Intel)
    [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
    [ -x /usr/local/bin/brew ] && eval "$(/usr/local/bin/brew shellenv)"
  fi
  command -v yt-dlp >/dev/null || brew install yt-dlp
  command -v ffmpeg >/dev/null || brew install ffmpeg
else
  echo "(Kein Mac erkannt – bitte yt-dlp und ffmpeg über deinen Paketmanager installieren, z. B. apt install ffmpeg yt-dlp)"
fi

echo "→ Installiere faster-whisper …"
pip3 install -q -U faster-whisper 2>/dev/null || pip3 install -q -U --break-system-packages faster-whisper

ZIEL="$HOME/.claude/skills/video-ansehen"
if [ "$HIER" != "$ZIEL" ]; then
  mkdir -p "$HOME/.claude/skills"
  rm -rf "$ZIEL"; cp -R "$HIER" "$ZIEL"
fi
chmod +x "$ZIEL/install.sh" "$ZIEL"/scripts/*.sh
echo
echo "✓ Fertig. Skill liegt in $ZIEL"
echo "  Starte Claude neu und schreibe: \"Schau dir das Video an: <YouTube-Link>\""
