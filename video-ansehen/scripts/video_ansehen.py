#!/usr/bin/env python3
"""Holt Infos + Transkript eines YouTube-Videos, mit mehreren Ausweichwegen.

Nutzung:
  video_ansehen.py "<LINK>"            # Link (youtu.be, watch?v=, shorts, embed, nur ID)
  video_ansehen.py --file datei.vtt    # eigene Untertitel/Transkript-Datei (.vtt .srt .txt)
  video_ansehen.py --stdin             # Transkript aus der Zwischenablage/Pipe
  Optionen: --lang de,en   --whisper (Ton herunterladen und selbst transkribieren)
"""
import argparse, glob, json, os, re, shutil, socket, subprocess, sys, tempfile, urllib.parse, urllib.request

OUT_DIR = os.path.expanduser("~/video-transkripte")
LONG = 30000  # ab so vielen Zeichen: in Teilen lesen


def video_id(s):
    s = s.strip()
    if re.fullmatch(r"[\w-]{11}", s):
        return s
    u = urllib.parse.urlparse(s if "//" in s else "https://" + s)
    if u.netloc.endswith("youtu.be"):
        return u.path.strip("/").split("/")[0][:11]
    q = urllib.parse.parse_qs(u.query)
    if "v" in q:
        return q["v"][0][:11]
    m = re.search(r"/(shorts|embed|live|v)/([\w-]{11})", u.path)
    return m.group(2) if m else None


def run(cmd, timeout=180):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:  # noqa
        return 1, "", str(e)


def pip_install(pkg):
    for extra in ([], ["--break-system-packages"]):
        c, _, _ = run([sys.executable, "-m", "pip", "install", "--user", "-q", "-U", pkg] + extra, 240)
        if c == 0:
            return True
    return False


def reachable(host="www.youtube.com"):
    try:
        socket.create_connection((host, 443), timeout=8).close()
        return True
    except Exception:
        pass
    try:  # Umgebung mit Proxy
        urllib.request.urlopen(f"https://{host}", timeout=8)
        return True
    except Exception as e:
        return "HTTP Error" in str(e)


def clean_subs(text):
    """VTT/SRT/TXT -> Zeilen mit [mm:ss], doppelte Zeilen entfernt."""
    out, seen, stamp = [], set(), None
    for raw in text.splitlines():
        raw = raw.strip()
        m = re.match(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,]\d+\s*-->", raw)
        if m:
            h, mi, s = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
            stamp = f"[{h*60+mi:02d}:{s:02d}]"
            continue
        if not raw or raw.isdigit() or raw.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        t = re.sub(r"<[^>]+>", "", raw).replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(f"{stamp} {t}" if stamp else t)
    return "\n".join(out)


def via_ytdlp(url, vid, langs):
    exe = shutil.which("yt-dlp")
    base = [exe] if exe else None
    if not base:
        if run([sys.executable, "-m", "yt_dlp", "--version"])[0] != 0 and not pip_install("yt-dlp"):
            return None, None, "yt-dlp lässt sich nicht installieren"
        base = [sys.executable, "-m", "yt_dlp"]
    tmp = tempfile.mkdtemp()
    c, o, e = run(base + ["--skip-download", "--no-warnings", "-J", url], 120)
    meta = {}
    if c == 0:
        try:
            j = json.loads(o)
            meta = {"Titel": j.get("title"), "Kanal": j.get("channel"), "Länge": j.get("duration_string"),
                    "Datum": j.get("upload_date"), "Beschreibung": j.get("description")}
            chapters = j.get("chapters") or []
            if chapters:
                meta["Kapitel"] = "\n".join(f"  {int(ch['start_time'])//60:02d}:{int(ch['start_time'])%60:02d} {ch['title']}" for ch in chapters)
        except Exception:
            pass
    else:
        return None, None, (e.strip().splitlines() or ["yt-dlp Fehler"])[-1]
    sl = ",".join(f"{l}.*,{l}" for l in langs)
    run(base + ["--skip-download", "--no-warnings", "--write-subs", "--write-auto-subs", "--sub-langs", sl,
                "--sub-format", "vtt/srt/best", "-o", f"{tmp}/%(id)s.%(ext)s", url], 180)
    files = sorted(glob.glob(f"{tmp}/*.vtt") + glob.glob(f"{tmp}/*.srt"))
    pick = None
    for l in langs:  # Sprache in Wunschreihenfolge, manuelle vor automatischen nicht unterscheidbar -> erste Treffer
        pick = next((f for f in files if f".{l}" in os.path.basename(f)), None)
        if pick:
            break
    pick = pick or (files[0] if files else None)
    text = clean_subs(open(pick, encoding="utf-8", errors="ignore").read()) if pick else None
    return meta, text, None


def via_transcript_api(vid, langs):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        if not pip_install("youtube-transcript-api"):
            return None, "youtube-transcript-api nicht installierbar"
        from youtube_transcript_api import YouTubeTranscriptApi
    try:
        try:
            items = YouTubeTranscriptApi().fetch(vid, languages=langs)  # neue API
            rows = [(i.start, i.text) for i in items]
        except AttributeError:
            items = YouTubeTranscriptApi.get_transcript(vid, languages=langs)  # alte API
            rows = [(i["start"], i["text"]) for i in items]
        return "\n".join(f"[{int(s)//60:02d}:{int(s)%60:02d}] {t}" for s, t in rows), None
    except Exception as e:
        return None, str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__


def via_oembed(vid):
    try:
        u = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://www.youtube.com/watch?v={vid}")
        j = json.load(urllib.request.urlopen(u, timeout=15))
        return {"Titel": j.get("title"), "Kanal": j.get("author_name")}
    except Exception:
        return None


def via_whisper(url, langs):
    base = shutil.which("yt-dlp")
    if not base or not shutil.which("ffmpeg"):
        return None, "für --whisper werden yt-dlp und ffmpeg gebraucht"
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        if not pip_install("faster-whisper"):
            return None, "faster-whisper nicht installierbar"
        from faster_whisper import WhisperModel
    tmp = tempfile.mkdtemp()
    c, _, e = run([base, "-x", "--audio-format", "mp3", "-o", f"{tmp}/a.%(ext)s", url], 900)
    f = glob.glob(f"{tmp}/a.*")
    if c != 0 or not f:
        return None, "Ton konnte nicht geladen werden"
    segs, _ = WhisperModel("small", compute_type="int8").transcribe(f[0], language=langs[0] if langs else None)
    return "\n".join(f"[{int(s.start)//60:02d}:{int(s.start)%60:02d}] {s.text.strip()}" for s in segs), None


BLOCKED = """\
!! KEIN ZUGRIFF AUF YOUTUBE !!
Das Netzwerk blockiert YouTube (z. B. Cloud-Umgebung mit Netzwerk-Sperre oder Firmen-Proxy). Das lässt sich
nicht umgehen. Lösungen, in dieser Reihenfolge:
  1. Nutzer fragen: Transkript einfügen (YouTube -> "...mehr" -> "Transkript anzeigen" -> kopieren),
     dann: video_ansehen.py --stdin   (oder Text direkt analysieren)
  2. Nutzer lädt Untertitel-Datei hoch (.vtt/.srt/.txt) -> video_ansehen.py --file <Datei>
  3. In der Cloud: Netzwerk-Einstellungen der Umgebung -> Allowed domains:
     www.youtube.com, youtu.be, i.ytimg.com, googlevideo.com
  4. Lokal ausführen (eigener Computer ohne Sperre) oder Gemini nutzen (kann YouTube direkt ansehen).
NICHTS erfinden: Inhalt des Videos nicht raten."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--lang", default="de,en")
    ap.add_argument("--whisper", action="store_true")
    a = ap.parse_args()
    langs = [l.strip() for l in a.lang.split(",") if l.strip()]
    meta, text, notes, vid = {}, None, [], None

    if a.file:
        text = clean_subs(open(a.file, encoding="utf-8", errors="ignore").read())
        vid = os.path.splitext(os.path.basename(a.file))[0]
        notes.append(f"Quelle: Datei {a.file}")
    elif a.stdin:
        text = sys.stdin.read().strip()
        vid = "eingefuegt"
        notes.append("Quelle: eingefügtes Transkript")
    elif a.url:
        vid = video_id(a.url)
        if not vid:
            sys.exit("FEHLER: Keine gültige YouTube-Video-ID im Link gefunden.")
        url = f"https://www.youtube.com/watch?v={vid}"  # entfernt ?si=... & Co.
        if not reachable():
            print(BLOCKED)
            sys.exit(3)
        m, t, err = via_ytdlp(url, vid, langs)
        if m:
            meta = m
        if err:
            notes.append(f"yt-dlp: {err}")
        text = t
        if not text:
            t2, err2 = via_transcript_api(vid, langs)
            if err2:
                notes.append(f"transcript-api: {err2}")
            text = t2
        if not meta:
            meta = via_oembed(vid) or {}
        if not text and a.whisper:
            t3, err3 = via_whisper(url, langs)
            if err3:
                notes.append(f"whisper: {err3}")
            text = t3
        if not text:
            notes.append("Kein Transkript gefunden (Video hat evtl. keine Untertitel, ist privat/altersbeschränkt "
                         "oder YouTube verlangt Anmeldung). Tipp: --whisper probieren, oder Transkript einfügen (--stdin).")
    else:
        ap.print_help()
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    print("===== INFOS =====")
    for k, v in meta.items():
        if v and k != "Beschreibung":
            print(f"{k}: {v}")
    if meta.get("Beschreibung"):
        print("\n===== BESCHREIBUNG =====\n" + meta["Beschreibung"][:3000])
    print("\n===== TRANSKRIPT =====")
    if text:
        path = os.path.join(OUT_DIR, f"{vid}.txt")
        open(path, "w", encoding="utf-8").write(text + "\n")
        if len(text) > LONG:
            print(f"(Lang: {len(text)} Zeichen. Erste {LONG} hier, Rest in Teilen lesen mit:\n"
                  f" python3 -c \"print(open('{path}').read()[{LONG}:{2*LONG}])\" usw.)\n")
            print(text[:LONG])
        else:
            print(text)
        print(f"\n(Gespeichert: {path})")
    else:
        print("(kein Transkript)")
    if notes:
        print("\n===== HINWEISE =====\n" + "\n".join(notes))


if __name__ == "__main__":
    main()
