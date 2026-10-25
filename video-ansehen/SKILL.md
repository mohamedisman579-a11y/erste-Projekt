---
name: video-ansehen
description: Wertet YouTube-Videos aus. Nutzen, wenn der Nutzer einen YouTube-Link schickt und sagt "schau dir das Video an", "fass das Video zusammen", "erklär das Video" oder "was wird im Video gesagt". Lädt mit yt-dlp Titel, Kanal, Beschreibung, Kapitel und Untertitel; gibt es keine Untertitel, wird der Ton heruntergeladen und lokal mit faster-whisper transkribiert. Kann auch Einzelbilder (Folien/Code) per ffmpeg aus dem Video holen.
---

# Video ansehen

Claude kann kein Video abspielen. Der Skill holt den **Text** des Videos (Infos, Kapitel, Transkript mit
Zeitstempeln) und optional **Einzelbilder**. Skripte liegen in `~/.claude/skills/video-ansehen/scripts/`.

## Ablauf

1. **Transkript holen** (Link unverändert übergeben, `?si=…` stört nicht):
   ```bash
   bash ~/.claude/skills/video-ansehen/scripts/transkript.sh "<LINK>"
   ```
   Das Skript macht automatisch:
   - a) Titel, Kanal, Länge, Beschreibung, Kapitel und vorhandene Untertitel laden (yt-dlp)
   - b) Gibt es **keine Untertitel**: Ton laden und lokal mit faster-whisper transkribieren
        (Modell `small`, Sprache wird automatisch erkannt)
   - c) Ausgabe mit Zeitstempeln `[mm:ss]`, gespeichert in `~/video-transkripte/<ID>.txt`
   - d) **Video über 45 Minuten:** Es zeigt nur Titel + Kapitel und lädt noch nichts.

2. **Bei langen Videos (Meldung „LANGES VIDEO“):** Dem Nutzer die Kapitel zeigen und **fragen, welchen
   Abschnitt** er genauer wissen will. Danach erst weiterverarbeiten:
   ```bash
   bash ~/.claude/skills/video-ansehen/scripts/transkript.sh "<LINK>" --abschnitt 12:00-30:00
   bash ~/.claude/skills/video-ansehen/scripts/transkript.sh "<LINK>" --alles   # nur wenn der Nutzer das will
   ```

3. **Bilder aus dem Video** (wenn Folien, Code, Diagramme, Formeln gezeigt werden und der Text allein nicht reicht):
   ```bash
   bash ~/.claude/skills/video-ansehen/scripts/bilder.sh "<LINK oder Datei>" 3:10 12:45
   ```
   Die JPG-Dateien liegen in `~/video-transkripte/bilder/`; mit dem Read-Tool ansehen und beschreiben.
   Passende Zeitstempel aus dem Transkript wählen (z. B. wenn „wie ihr hier seht“ gesagt wird).

4. **Fehlermeldungen**
   - `yt-dlp`/`ffmpeg` fehlt → `bash ~/.claude/skills/video-ansehen/install.sh`
   - „YouTube gesperrt“ / Proxy / 403 → Netzwerk blockiert YouTube. Nicht umgehen. Nutzer bitten, das
     Transkript einzufügen („…mehr“ → „Transkript anzeigen“) oder den Skill auf seinem eigenen Rechner zu nutzen.
   - Anmeldung/Alter nötig, Video privat → ehrlich sagen, dass es nicht lesbar ist.

## Antwort an den Nutzer (Deutsch, einfach, kurz)

- **Worum geht's?** (1–2 Sätze)
- **Die wichtigsten Punkte** (Stichpunkte mit Zeitmarken wie [03:20])
- **Fazit / Was du mitnehmen kannst**
- Sagen, woher der Text stammt (YouTube-Untertitel manuell/automatisch oder Whisper) und anbieten:
  Fragen beantworten, Lernkarten/Quiz, Bilder zu bestimmten Stellen.

## Regeln

- Nur Inhalte aus Infos/Transkript/Bildern verwenden. **Nie** Inhalt erraten oder erfinden.
- Automatische Untertitel und Whisper machen Fehler bei Fachbegriffen und Zahlen – bei Unsicherheit darauf hinweisen.
- Lange Videos nie ungefragt komplett verarbeiten.
