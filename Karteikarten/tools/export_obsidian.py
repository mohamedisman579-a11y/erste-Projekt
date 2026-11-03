"""Erzeugt einen Obsidian-Ordner: eine Notiz je Teil (Karten im Format des Spaced-Repetition-Plugins) plus Übersicht."""
import re, sys, os, datetime
src, outdir = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()
os.makedirs(outdir, exist_ok=True)
names = {'1': 'Kap 1 Allgemeine Grundlagen', '2': 'Kap 2 Grundbegriffe und Einheiten', '3': 'Kap 3 Mechanisches Verhalten',
         '4': 'Kap 4 Wärme und Kälte', '5': 'Formelsammlung', '6': 'Altklausuren Feb 2024 und Juli 2024'}
notes = {k: [] for k in names}
teil = None
for block in re.split(r'\n---\n', text):
    t = re.findall(r'^# TEIL (\d)', block, re.M)
    if t: teil = t[-1]
    m = re.search(r'^### (Karte [^\n]*)\n\*\*Frage:\*\*\s*(.*?)\n\n\*\*Antwort[^\n]*?\*\*:?[ \t]*\n?(.*)$', block, re.S | re.M)
    if not m: continue
    title, q, a = m.groups()
    a = re.split(r'\n# TEIL|\n## ', a)[0].strip()
    q2 = re.sub(r"\n\s*\n", "\n", q.strip()); a2 = re.sub(r"\n\s*\n", "\n", a)
    notes[teil].append(f"### {title}\n\n{q2}\n?\n{a2}\n")
today = datetime.date.today().isoformat()
for k, cards in notes.items():
    fn = f"BSK1 – {names[k]}.md"
    head = (f"---\nfach: Baustoffkunde 1\nthema: {names[k]}\nkarten: {len(cards)}\nquelle: Vorlesungsfolien Prof. Marquardt (HAWK), Übungsfragen, Altklausuren 02/2024 und 07/2024\n"
            f"aktualisiert: {today}\ntags: [baustoffkunde, karteikarten]\n---\n\n#flashcards/baustoffkunde\n\n"
            f"# {names[k]}\n\nZurück zur [[BSK1 – Übersicht]]\n\nFormat: Frage, dann eine Zeile mit `?`, dann die Antwort.\n\n")
    open(os.path.join(outdir, fn), 'w', encoding='utf-8').write(head + "\n".join(cards))
idx = ["---\nfach: Baustoffkunde 1\ntags: [baustoffkunde, übersicht]\n---\n", "# BSK1 – Übersicht", "",
       "Karteikarten zu Baustoffkunde 1 (HAWK, Prof. Marquardt), Kapitel 1–4. Quellen sind nur die Vorlesungsfolien, die Übungsfragen und die Altklausuren vom 07.02.2024 und 30.07.2024.", "",
       "Zeichen: ⭐ Übungsfrage · 🧮 Rechenaufgabe · 📝 Altklausur-Aufgabe", "", "## Notizen", ""]
order = ['6', '3', '4', '1', '2', '5']
for k in order:
    idx.append(f"- [[BSK1 – {names[k]}]] ({len(notes[k])} Karten)")
idx += ["", f"Gesamt: {sum(len(v) for v in notes.values())} Karten", "", "## Lernreihenfolge", "",
        "1. Altklausuren (kommen fast immer dran)", "2. Kap 3 Mechanik (ca. 18 Klausurpunkte)", "3. Kap 4 Wärme (ca. 10 Punkte)",
        "4. Kap 1 Grundlagen (ca. 11 Punkte)", "5. Kap 2 Grundbegriffe, dann die Formelsammlung", "",
        "## Lernplan", "", "- Woche 1–2: 10 neue Karten pro Tag, plus Wiederholungen (ca. 30 min)",
        "- ab Woche 3: nur Wiederholungen (15–20 min)", "- letzte 2 Wochen: 2× pro Woche eine Altklausur auf Papier schreiben", "",
        "## Hinweise aus den Korrekturen (Juli 2024)", "",
        "- α_T von Stahl und Beton: 10 · 10⁻⁶ 1/K", "- ‰ heißt mal 1.000, nicht mal 100", "- Einheiten immer hinschreiben (1/K, N/mm²)",
        "- Verwendbarkeitsnachweise: abZ, abP, ZiE", "- Kriechen: Diagramme σ-t und ε-t zeichnen",
        "- λ hängt ab von Struktur, Porosität, Rohdichte, Temperatur und Feuchtegehalt", ""]
open(os.path.join(outdir, "BSK1 – Übersicht.md"), 'w', encoding='utf-8').write("\n".join(idx))
print({names[k]: len(v) for k, v in notes.items()})
