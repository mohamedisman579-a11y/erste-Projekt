---
name: video-ansehen
description: YouTube-Video "ansehen" – holt Titel, Beschreibung und Transkript (Untertitel) eines YouTube-Links und erklärt bzw. fasst den Inhalt zusammen. Nutzen, wenn der Nutzer einen YouTube-Link schickt und sagt "schau dir das Video an", "erklär das Video", "fass das Video zusammen".
---

# Video ansehen

Claude kann Videos nicht abspielen. Dieser Skill holt stattdessen den **Text** des Videos
(Titel, Kanal, Beschreibung, Transkript) und arbeitet damit.

## Ablauf

1. Transkript holen:
   ```bash
   bash ~/.claude/skills/video-ansehen/scripts/transkript.sh "<YOUTUBE-LINK>"
   ```
   Das Skript gibt Titel, Kanal, Länge, Beschreibung und das Transkript als Text aus
   und speichert alles unter `~/video-transkripte/<VIDEO-ID>.txt`.

2. Wenn das Skript meldet, dass `yt-dlp` fehlt: `bash ~/.claude/skills/video-ansehen/install.sh` ausführen.

3. Wenn **kein Transkript** vorhanden ist: Dem Nutzer ehrlich sagen, dass das Video keine
   Untertitel hat, und nur mit Titel + Beschreibung arbeiten. Nichts erfinden.

4. Antwort auf Deutsch, einfach und kurz:
   - **Worum geht's?** (1–2 Sätze)
   - **Die wichtigsten Punkte** (Stichpunkte, mit ungefähren Zeitangaben wenn möglich)
   - **Fazit / Was du mitnehmen kannst**
   - Angebot: Fragen dazu beantworten, Lernkarten oder Quiz erstellen.

## Regeln

- Nur Inhalte aus Transkript/Beschreibung verwenden, keine erfundenen Details.
- Bei Lernvideos (Mathe, Mechanik, Baustoffe …) gern Schritt für Schritt erklären.
