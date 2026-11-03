"""Baut aus der Markdown-Kartei eine Anki-Datei (.apkg) mit Unterstapeln je Teil und Tags."""
import re, subprocess, sys, genanki
src, out = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()

def md2html(md):
    return subprocess.run(['pandoc', '-f', 'gfm+hard_line_breaks', '-t', 'html'], input=md, capture_output=True, text=True, check=True).stdout

css = """.card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:18px;line-height:1.45;text-align:left;color:#1d1d1f;background:#fff;padding:6px}
.meta{font-size:12px;color:#777;margin-bottom:8px}
table{border-collapse:collapse;font-size:15px;margin:6px 0}td,th{border:1px solid #bbb;padding:3px 6px;vertical-align:top}
hr#answer{margin:14px 0}
.nightMode .card,.night_mode .card{color:#eee;background:#1e1e1e}.nightMode td,.nightMode th{border-color:#555}"""
model = genanki.Model(1607392319, 'Baustoffkunde Frage/Antwort',
    fields=[{'name': 'Frage'}, {'name': 'Antwort'}, {'name': 'Info'}],
    templates=[{'name': 'Karte',
                'qfmt': '<div class="meta">{{Info}}</div>{{Frage}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Antwort}}'}], css=css)

decknames = {'1': '1 Allgemeine Grundlagen', '2': '2 Grundbegriffe und Einheiten', '3': '3 Mechanisches Verhalten',
             '4': '4 Wärme und Kälte', '5': '5 Formelsammlung', '6': '0 Altklausuren (kommen fast immer!)'}
decks = {k: genanki.Deck(2059400110 + int(k), 'Baustoffkunde I::' + v) for k, v in decknames.items()}
teil = None; n = 0
for block in re.split(r'\n---\n', text):
    t = re.findall(r'^# TEIL (\d)', block, re.M)
    if t: teil = t[-1]
    m = re.search(r'^### (Karte [^\n]*)\n\*\*Frage:\*\*\s*(.*?)\n\n\*\*Antwort[^\n]*?\*\*:?[ \t]*\n?(.*)$', block, re.S | re.M)
    if not m: continue
    title, q, a = m.groups()
    a = re.split(r'\n# TEIL|\n## ', a)[0].strip()
    tags = ['Kap' + teil] if teil in '1234' else []
    if '⭐' in title: tags.append('Uebungsfrage')
    if '🧮' in title: tags.append('Rechnen')
    if '📝' in title: tags.append('Altklausur')
    if teil == '6': tags.append('Altklausur')
    tags = sorted(set(tags))
    num = re.match(r'Karte (\w+)', title).group(1)
    info = f'{decknames[teil]} · {title}'
    note = genanki.Note(model=model, fields=[md2html(q), md2html(a), info], tags=tags, guid=genanki.guid_for('bsk1', num))
    decks[teil].add_note(note); n += 1
genanki.Package(list(decks.values())).write_to_file(out)
print(n, 'Karten ->', out)
