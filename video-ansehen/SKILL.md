---
name: video-ansehen
description: YouTube-Video "ansehen" – holt Titel, Beschreibung, Kapitel und Transkript (Untertitel) eines YouTube-Links und erklärt bzw. fasst den Inhalt zusammen. Hat mehrere Ausweichwege (yt-dlp, transcript-api, Whisper, eingefügtes Transkript, Untertitel-Datei). Nutzen, wenn der Nutzer einen YouTube-Link schickt oder sagt "schau dir das Video an", "erklär das Video", "fass das Video zusammen", "was wird im Video gesagt".
---

# Video ansehen

Claude kann kein Video abspielen. Der Skill holt den **Text** des Videos (Titel, Beschreibung, Kapitel,
Untertitel/Transkript) und arbeitet damit. Skript: `~/.claude/skills/video-ansehen/scripts/video_ansehen.py`
(bei Cloud-Sessions: dort, wo der Skill entpackt wurde).

## Ablauf (immer in dieser Reihenfolge)

1. **Link nehmen**, wie er ist (`youtu.be/...?si=...`, `watch?v=`, Shorts – alles geht, Zusatzteile wie `si=` werden entfernt):
   ```bash
   python3 ~/.claude/skills/video-ansehen/scripts/video_ansehen.py "<LINK>"
   ```
   Das Skript probiert selbst nacheinander: yt-dlp → youtube-transcript-api → oEmbed (nur Titel).
   Fehlende Programme installiert es automatisch (`pip --user`).

2. **Meldung "KEIN ZUGRIFF AUF YOUTUBE"** (Netzwerk gesperrt, typisch in Cloud-Sessions):
   Nicht versuchen, das zu umgehen (keine Proxy-/TLS-Tricks). Dem Nutzer kurz sagen und anbieten:
   - Transkript einfügen: YouTube → „…mehr“ → „Transkript anzeigen“ → kopieren → hier einfügen
   - oder Untertitel-Datei (.vtt/.srt/.txt) hochladen → `video_ansehen.py --file <Datei>`
   - oder in den Umgebungs-Einstellungen (Network access → Allowed domains) freischalten:
     `www.youtube.com`, `youtu.be`, `i.ytimg.com`, `googlevideo.com`
   - oder den Skill lokal auf dem eigenen Computer ausführen / Gemini nutzen
   Eingefügten Text direkt analysieren (oder mit `--stdin` bereinigen).

3. **Kein Transkript, aber Zugriff da** (Video ohne Untertitel): erneut mit `--whisper` versuchen
   (lädt den Ton und transkribiert lokal; braucht ffmpeg, dauert länger). Klappt das nicht: ehrlich sagen,
   dass nur Titel/Beschreibung vorliegen, und darauf beschränken.

4. **Sprache**: Standard ist `--lang de,en`. Anderes Video → z. B. `--lang es,en`.

5. **Langes Transkript** (> 30.000 Zeichen): Das Skript zeigt den Anfang und nennt die Datei
   (`~/video-transkripte/<ID>.txt`); den Rest in Teilen lesen, dann zusammenfassen.

## Antwort an den Nutzer (Deutsch, einfach, kurz)

- **Worum geht's?** (1–2 Sätze)
- **Die wichtigsten Punkte** (Stichpunkte, mit Zeitmarken wie [03:20])
- **Fazit / Was du mitnehmen kannst**
- Angebot: Fragen beantworten, Lernkarten, Quiz oder Übungsaufgaben (bei Uni-Stoff passende Skills wie
  bauingenieur-dozent oder feynman-lernschleife nutzen).

## Regeln

- Nur Inhalte aus Transkript/Beschreibung verwenden. **Nie** den Inhalt raten oder erfinden.
- Automatische Untertitel enthalten Fehler (Fachbegriffe, Zahlen) – bei Unsicherheit darauf hinweisen.
- Immer sagen, woher der Inhalt stammt (Transkript, nur Beschreibung, eingefügter Text).
