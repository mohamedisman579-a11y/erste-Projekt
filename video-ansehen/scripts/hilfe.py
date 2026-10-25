#!/usr/bin/env python3
"""Hilfsfunktionen für video-ansehen: meta | vtt | whisper"""
import json, re, sys


def mmss(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60:02d}:{sec % 60:02d}"


def parse_zeit(s):
    """'90', '1:30' oder '1:02:03' -> Sekunden"""
    teile = [int(x) for x in s.split(":")]
    sek = 0
    for t in teile:
        sek = sek * 60 + t
    return sek


def meta(json_datei, modus):
    """modus 'info' -> Infos drucken; 'dauer' -> Sekunden; 'sprache' -> bestes Untertitel-Kürzel oder leer;
    'quelle' -> manuell|auto|keine"""
    j = json.load(open(json_datei, encoding="utf-8"))
    if modus == "dauer":
        print(int(j.get("duration") or 0))
    elif modus in ("sprache", "quelle"):
        manuell = list((j.get("subtitles") or {}).keys())
        auto = list((j.get("automatic_captions") or {}).keys())
        orig = [k for k in auto if k.endswith("-orig")]
        lang = (j.get("language") or "").split("-")[0]
        wahl, quelle = "", "keine"
        if manuell:
            wahl = next((k for k in manuell if k.split("-")[0] == lang), None) or next(
                (k for k in manuell if k.split("-")[0] in ("de", "en")), manuell[0])
            quelle = "manuell"
        elif orig:
            wahl, quelle = orig[0], "auto"
        elif auto:
            wahl = next((k for k in (lang, "de", "en") if k in auto), "")
            quelle = "auto" if wahl else "keine"
        print(wahl if modus == "sprache" else quelle)
    else:
        print(f"Titel:   {j.get('title')}")
        print(f"Kanal:   {j.get('channel') or j.get('uploader')}")
        print(f"Länge:   {j.get('duration_string') or mmss(j.get('duration') or 0)}")
        print(f"Datum:   {j.get('upload_date')}")
        print(f"Sprache: {j.get('language') or 'unbekannt'}")
        kap = j.get("chapters") or []
        if kap:
            print("\nKapitel:")
            for k in kap:
                print(f"  {mmss(k['start_time'])}  {k['title']}")
        beschr = (j.get("description") or "").strip()
        if beschr:
            print("\nBeschreibung:\n" + beschr[:3000])


def lies_vtt(text):
    """(sekunden, text)-Liste aus VTT/SRT, ohne Duplikate (YouTube-Auto-Untertitel wiederholen Zeilen)."""
    out, gesehen, start = [], set(), 0
    for raw in text.splitlines():
        raw = raw.strip()
        m = re.match(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,]\d+\s*-->", raw)
        if m:
            start = int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            continue
        if not raw or raw.isdigit() or raw.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        t = re.sub(r"<[^>]+>", "", raw).replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<").strip()
        if t and t not in gesehen:
            gesehen.add(t)
            out.append((start, t))
    return out


def vtt(datei, von, bis):
    for s, t in lies_vtt(open(datei, encoding="utf-8", errors="ignore").read()):
        if s >= von and (bis <= 0 or s <= bis):
            print(f"[{mmss(s)}] {t}")


def whisper(audio, offset):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("FEHLER: faster-whisper fehlt. Installieren: pip3 install faster-whisper (--break-system-packages)")
    modell = WhisperModel("small", compute_type="int8")  # Sprache wird automatisch erkannt
    segmente, info = modell.transcribe(audio, language=None, vad_filter=True)
    print(f"(Whisper: Sprache erkannt = {info.language}, Sicherheit {info.language_probability:.0%})", file=sys.stderr)
    for s in segmente:
        print(f"[{mmss(s.start + offset)}] {s.text.strip()}")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "meta":
        meta(args[0], args[1] if len(args) > 1 else "info")
    elif cmd == "vtt":
        vtt(args[0], int(args[1]), int(args[2]))
    elif cmd == "whisper":
        whisper(args[0], int(args[1]) if len(args) > 1 else 0)
    elif cmd == "zeit":
        print(parse_zeit(args[0]))
    else:
        sys.exit("unbekannter Befehl")
