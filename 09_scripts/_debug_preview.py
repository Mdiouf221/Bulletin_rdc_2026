"""Script de diagnostic du serveur de prévisualisation."""
import re, markdown, unicodedata
from markdown.extensions.toc import TocExtension
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent

with open(BASE / '10_output/bulletin_complet_travail.md', encoding='utf-8') as f:
    md_text = f.read()

# --- Normalisation sans accents pour comparaison robuste ---
def norm(s):
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().strip()

STATUS_CLASSES = {
    norm('à rédiger'):           ('status-structure', 'À rédiger'),
    norm('à compléter'):         ('status-structure', 'À compléter'),
    norm('structure initiale'):  ('status-structure', 'Structure initiale'),
    norm('notes développées'):   ('status-notes',     'Notes développées'),
    norm('rédigé'):              ('status-redige',     'Rédigé'),
    norm('révisé'):              ('status-revise',     'Révisé'),
    norm('validé'):              ('status-valide',     'Validé'),
}

print("Clés STATUS_CLASSES:", list(STATUS_CLASSES.keys()))

# --- Build status map ---
lines = md_text.split('\n')
mapping = {}
i = 0
while i < len(lines):
    m = re.match(r'^#{1,6}\s+(.+)$', lines[i])
    if m:
        heading_text = m.group(1).strip()
        in_note = False
        for j in range(i + 1, min(i + 40, len(lines))):
            if '<!-- NOTE_INTERNE' in lines[j]:
                in_note = True
                continue
            if not in_note:
                continue
            if '-->' in lines[j]:
                break
            sm = re.search(r'[Ss]tatut\s*:\s*(.*)', lines[j])
            if sm:
                raw = sm.group(1).strip()
                if not raw and j + 1 < len(lines):
                    raw = lines[j + 1].strip()
                raw = re.sub(r'\s*-->.*$', '', raw).strip()
                key = norm(raw)
                print(f"  Heading: [{heading_text[:50]}]  raw=[{raw}]  key=[{key}]  match={key in STATUS_CLASSES}")
                if key in STATUS_CLASSES:
                    mapping[heading_text] = STATUS_CLASSES[key]
                break
    i += 1

print(f"\nStatus map: {len(mapping)} entrées")

# --- Convert markdown ---
md_proc = markdown.Markdown(extensions=['tables', 'fenced_code', TocExtension(title='', toc_depth=3)])
body = md_proc.convert(md_text)

# --- Inject dots ---
dot_count = 0
for heading_text, (cls, label) in mapping.items():
    dot = f'<span class="status-dot {cls}" title="{label}">&#9679;</span> '
    pattern = r'(<h[1-6][^>]*>)(' + re.escape(heading_text) + r')(</h[1-6]>)'
    new_body, n = re.subn(pattern, lambda mo, d=dot: mo.group(1) + d + mo.group(2) + mo.group(3), body)
    if n > 0:
        dot_count += n
        body = new_body
    else:
        # Debug: chercher le titre dans le HTML pour voir la vraie forme
        found = re.findall(r'<h[1-6][^>]*>.*?' + re.escape(heading_text[:15]) + r'.*?</h[1-6]>', body)
        if found:
            print(f"  NON INJECTÉ: [{heading_text[:40]}] -> HTML: {found[0][:100]}")

print(f"\nDots injectés: {dot_count}")

# --- Vérifier JS dans le serveur ---
with open(BASE / '09_scripts/serveur_preview.py', encoding='utf-8') as f:
    srv = f.read()
print(f"\nJS makeCollapsible présent: {'makeCollapsible' in srv}")
print(f"JS status-legend présent:   {'status-legend' in srv}")
print(f"JS source-tooltip présent:  {'source-tooltip' in srv}")
print(f"page-indicator CSS présent: {'page-indicator' in srv}")
