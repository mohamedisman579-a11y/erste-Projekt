#!/usr/bin/env bash
# Extrahiert Einzelbilder (Folien/Code) aus einem Video an bestimmten Zeitstempeln.
# Nutzung: bilder.sh <YOUTUBE-LINK oder Videodatei> <Zeit> [<Zeit> ...]
#   Zeit z. B. 90, 1:30 oder 1:02:03.   Beispiel: bilder.sh "https://youtu.be/XYZ" 0:45 3:10 12:00
# Ergebnis: JPG-Dateien in ~/video-transkripte/bilder/ (Claude kann sie danach ansehen/lesen).
set -euo pipefail
HIER="$(cd "$(dirname "$0")" && pwd)"
QUELLE="${1:-}"; shift || true
[ -n "$QUELLE" ] && [ $# -gt 0 ] || { echo "Nutzung: bilder.sh <LINK|Datei> <Zeit> [<Zeit> ...]" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "FEHLER: ffmpeg fehlt. Bitte ./install.sh ausführen." >&2; exit 2; }

AUS="$HOME/video-transkripte/bilder"; mkdir -p "$AUS"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

if [ -f "$QUELLE" ]; then
  EINGABE="$QUELLE"; NAME="$(basename "${QUELLE%.*}")"
else
  command -v yt-dlp >/dev/null || { echo "FEHLER: yt-dlp fehlt." >&2; exit 2; }
  NAME="$(yt-dlp --skip-download --no-playlist --print id "$QUELLE" | head -n1)"
  # Video in 720p laden (Folien/Code sind darin gut lesbar); ohne Ton, spart Zeit
  yt-dlp --no-warnings --no-playlist -f "bv*[height<=720]/b[height<=720]/b" -o "$TMP/video.%(ext)s" "$QUELLE" >/dev/null
  EINGABE="$(ls "$TMP"/video.* | head -n1)"
fi

for Z in "$@"; do
  SEK="$(python3 "$HIER/hilfe.py" zeit "$Z")"
  DATEI="$AUS/${NAME}_$(printf '%02d-%02d' $((SEK / 60)) $((SEK % 60))).jpg"
  ffmpeg -loglevel error -y -ss "$SEK" -i "$EINGABE" -frames:v 1 -q:v 2 "$DATEI"
  echo "$DATEI"
done
