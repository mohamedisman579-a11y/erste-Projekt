#!/usr/bin/env bash
# Holt Metadaten und Transkript eines YouTube-Videos als Text.
# Nutzung: transkript.sh "<YOUTUBE-LINK>"
set -euo pipefail

URL="${1:-}"
if [ -z "$URL" ]; then
  echo "Nutzung: transkript.sh \"<YOUTUBE-LINK>\"" >&2
  exit 1
fi

if command -v yt-dlp >/dev/null 2>&1; then
  YTDLP=(yt-dlp)
elif python3 -m yt_dlp --version >/dev/null 2>&1; then
  YTDLP=(python3 -m yt_dlp)
else
  echo "FEHLER: yt-dlp ist nicht installiert. Bitte install.sh ausführen." >&2
  exit 2
fi

OUT_DIR="$HOME/video-transkripte"
mkdir -p "$OUT_DIR"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

ID="$("${YTDLP[@]}" --skip-download --print id "$URL")"

echo "===== INFOS ====="
"${YTDLP[@]}" --skip-download \
  --print "Titel: %(title)s" \
  --print "Kanal: %(channel)s" \
  --print "Länge: %(duration_string)s" \
  --print "Hochgeladen: %(upload_date)s" \
  "$URL"
echo
echo "===== BESCHREIBUNG ====="
"${YTDLP[@]}" --skip-download --print "%(description)s" "$URL"
echo

# Untertitel holen: zuerst Deutsch, dann Englisch, manuelle und automatische.
"${YTDLP[@]}" --skip-download --write-subs --write-auto-subs \
  --sub-langs "de.*,de,en.*,en" --sub-format vtt \
  -o "$TMP/%(id)s.%(ext)s" "$URL" >/dev/null 2>&1 || true

VTT="$(ls "$TMP"/*.de*.vtt 2>/dev/null | head -n1 || true)"
[ -z "$VTT" ] && VTT="$(ls "$TMP"/*.vtt 2>/dev/null | head -n1 || true)"

echo "===== TRANSKRIPT ====="
if [ -z "$VTT" ]; then
  echo "(Kein Transkript/keine Untertitel für dieses Video verfügbar.)"
  exit 0
fi

# VTT in lesbaren Text mit Zeitmarken umwandeln, doppelte Zeilen entfernen.
python3 - "$VTT" "$OUT_DIR/$ID.txt" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
lines, seen, stamp = [], set(), None
for raw in open(src, encoding="utf-8"):
    raw = raw.strip()
    m = re.match(r"(\d{2}):(\d{2}):(\d{2})\.\d+ -->", raw)
    if m:
        h, mi, s = map(int, m.groups())
        stamp = f"[{h*60+mi:02d}:{s:02d}]"
        continue
    if not raw or raw.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
        continue
    text = re.sub(r"<[^>]+>", "", raw).strip()
    if text and text not in seen:
        seen.add(text)
        lines.append(f"{stamp} {text}" if stamp else text)
out = "\n".join(lines)
open(dst, "w", encoding="utf-8").write(out + "\n")
print(out)
PY

echo
echo "(Gespeichert unter: $OUT_DIR/$ID.txt)"
