"""Exportiert die Karteikarten aus der Markdown-Datei als CSV/TSV für StudySmarter (Frage | Antwort)."""
import csv, re, sys
src, outbase = sys.argv[1], sys.argv[2]
text = open(src, encoding='utf-8').read()
cards = []
kapitel = ''
for block in re.split(r'\n---\n', text):
    m_k = re.findall(r'^# (TEIL .*)$', block, re.M)
    if m_k: kapitel = m_k[-1]
    m = re.search(r'^### (Karte [^\n]*)\n\*\*Frage:\*\*\s*(.*?)\n\n\*\*Antwort[^\n]*?\*\*:?\s*(.*)$', block, re.S | re.M)
    if not m: continue
    title, q, a = m.groups()
    def clean(t):
        t = re.sub(r'^## .*$', '', t, flags=re.M)
        t = re.sub(r'^# .*$', '', t, flags=re.M)
        t = re.sub(r'^\|[-| ]+\|$', '', t, flags=re.M)          # Tabellen-Trennzeilen
        t = re.sub(r'^\|\s*(.*?)\s*\|$', lambda mm: ' | '.join(c.strip() for c in mm.group(1).split('|')), t, flags=re.M)
        t = t.replace('**', '').replace('*', '')
        t = re.sub(r'\n{3,}', '\n\n', t)
        return t.strip()
    tags = ('⭐ ' if '⭐' in title else '') + ('🧮 ' if '🧮' in title else '')
    front = f"{tags}{clean(q)}"
    back = clean(a)
    cards.append((front, back, kapitel.title()))
for name, delim in ((outbase + '.csv', ';'), (outbase + '.tsv', '\t')):
    with open(name, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=delim, quoting=csv.QUOTE_ALL)
        for c in cards: w.writerow(c[:2])
print(len(cards), 'Karten exportiert')
