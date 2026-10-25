#!/usr/bin/env bash
# Holt Infos + Transkript (mit Zeitstempeln) eines YouTube-Videos.
# Nutzung: transkript.sh <LINK> [--abschnitt VON-BIS] [--alles]
#   --abschnitt 10:00-25:30   nur diesen Teil (auch bei langen Videos)
#   --alles                   auch Videos über 45 Min komplett verarbeiten
set -euo pipefail

LIMIT_SEK=2700   # 45 Minuten
HIER="$(cd "$(dirname "$0")" && pwd)"
URL="${1:-}"; shift || true
VON=0; BIS=0; ALLES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --abschnitt) VON=$(python3 "$HIER/hilfe.py" zeit "${2%-*}"); BIS=$(python3 "$HIER/hilfe.py" zeit "${2#*-}"); shift 2 ;;
    --alles) ALLES=1; shift ;;
    *) echo "Unbekannte Option: $1" >&2; exit 1 ;;
  esac
done
[ -n "$URL" ] || { echo "Nutzung: transkript.sh <YOUTUBE-LINK> [--abschnitt VON-BIS] [--alles]" >&2; exit 1; }

for prog in yt-dlp python3; do
  command -v "$prog" >/dev/null || { echo "FEHLER: $prog fehlt. Bitte ./install.sh ausführen." >&2; exit 2; }
done

AUS="$HOME/video-transkripte"; mkdir -p "$AUS"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 1) Metadaten
if ! yt-dlp --skip-download --no-warnings --no-playlist -J "$URL" > "$TMP/meta.json" 2> "$TMP/fehler.txt"; then
  echo "FEHLER: Video-Infos konnten nicht geladen werden:"; tail -n 3 "$TMP/fehler.txt"
  if grep -qiE "proxy|tunnel|resolve|connect|network|403" "$TMP/fehler.txt"; then
    echo
    echo "-> Wahrscheinlich ist YouTube in diesem Netzwerk gesperrt. Lösung: Skill auf dem eigenen Computer ausführen,"
    echo "   oder Transkript manuell einfügen (YouTube: '...mehr' -> 'Transkript anzeigen')."
  fi
  exit 3
fi
ID="$(yt-dlp --skip-download --no-playlist --print id "$URL" 2>/dev/null | head -n1)"
DAUER="$(python3 "$HIER/hilfe.py" meta "$TMP/meta.json" dauer)"

echo "===== INFOS ====="
python3 "$HIER/hilfe.py" meta "$TMP/meta.json" info
echo

# 2) Langes Video: erst nur Überblick, dann nachfragen
if [ "$DAUER" -gt "$LIMIT_SEK" ] && [ "$ALLES" -eq 0 ] && [ "$BIS" -eq 0 ]; then
  echo "===== LANGES VIDEO ($((DAUER / 60)) Min) ====="
  echo "Das Video ist länger als 45 Minuten. Es wurde noch KEIN Transkript geladen."
  echo "-> Nutzer fragen, welchen Abschnitt er genauer wissen will (Kapitel oben oder Zeitraum),"
  echo "   dann: transkript.sh \"$URL\" --abschnitt VON-BIS    (z. B. --abschnitt 12:00-30:00)"
  echo "   oder ganz: transkript.sh \"$URL\" --alles"
  exit 0
fi

# 3) Untertitel
SPRACHE="$(python3 "$HIER/hilfe.py" meta "$TMP/meta.json" sprache)"
QUELLE="$(python3 "$HIER/hilfe.py" meta "$TMP/meta.json" quelle)"
TEXT=""
if [ -n "$SPRACHE" ]; then
  yt-dlp --skip-download --no-warnings --no-playlist --write-subs --write-auto-subs \
    --sub-langs "$SPRACHE" --sub-format "vtt/best" -o "$TMP/sub" "$URL" >/dev/null 2>&1 || true
  VTT="$(ls "$TMP"/sub*.vtt 2>/dev/null | head -n1 || true)"
  if [ -n "$VTT" ]; then
    TEXT="$(python3 "$HIER/hilfe.py" vtt "$VTT" "$VON" "$BIS")"
    HERKUNFT="YouTube-Untertitel ($QUELLE, Sprache: $SPRACHE)"
  fi
fi

# 4) Keine Untertitel -> Ton laden und lokal mit Whisper transkribieren
if [ -z "$TEXT" ]; then
  command -v ffmpeg >/dev/null || { echo "FEHLER: ffmpeg fehlt (für Whisper nötig). Bitte ./install.sh ausführen." >&2; exit 2; }
  echo "(Keine Untertitel vorhanden – lade Ton und transkribiere lokal mit Whisper 'small'. Das dauert etwas …)" >&2
  ABSCHNITT=()
  [ "$BIS" -gt 0 ] && ABSCHNITT=(--download-sections "*${VON}-${BIS}")
  yt-dlp --no-warnings --no-playlist -x --audio-format mp3 "${ABSCHNITT[@]}" -o "$TMP/ton.%(ext)s" "$URL" >/dev/null 2>"$TMP/fehler.txt" \
    || { echo "FEHLER: Ton konnte nicht geladen werden:"; tail -n 3 "$TMP/fehler.txt"; exit 3; }
  TEXT="$(python3 "$HIER/hilfe.py" whisper "$TMP/ton.mp3" "$VON")"
  HERKUNFT="lokal mit faster-whisper (Modell small, Sprache automatisch erkannt)"
fi

echo "===== TRANSKRIPT ====="
echo "Quelle: $HERKUNFT"
[ "$BIS" -gt 0 ] && echo "Abschnitt: $VON s – $BIS s"
echo
echo "$TEXT" | tee "$AUS/$ID.txt"
echo
echo "(Gespeichert: $AUS/$ID.txt)"
