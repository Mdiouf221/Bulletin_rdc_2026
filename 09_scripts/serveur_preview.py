"""
serveur_preview.py
------------------
Serveur de prévisualisation du bulletin dans le navigateur.

L'éditeur visuel expose uniquement les passages de texte : les balises,
les annotations et les tableaux sont conservés côté serveur. Les sauvegardes
portent sur le corps public des fichiers configurés et ne reçoivent jamais de HTML du navigateur.

Surveille tous les fichiers Markdown et YAML du workspace.
Dès qu'un fichier est modifié :
  1. L'assembleur est relancé automatiquement.
  2. La page HTML est régénérée.
  3. Le navigateur est rafraîchi sans intervention manuelle.

Usage :
    python 09_scripts/serveur_preview.py

Ouvrir ensuite dans le navigateur :
    http://localhost:8765

Arrêt : Ctrl+C dans le terminal.

Dépendances :
    pip install markdown watchdog
"""

import http.server
import threading
import tempfile
import subprocess
import pathlib
import queue
import json
import hashlib
import html as html_lib
from html.parser import HTMLParser
import os
import re
import sys
import sqlite3
import webbrowser
import time
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    import markdown
    from markdown.extensions.toc import TocExtension
except ImportError:
    print("[ERREUR] Module 'markdown' requis.\n"
          "         Installer avec : pip install markdown")
    sys.exit(1)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("[ERREUR] Module 'watchdog' requis.\n"
          "         Installer avec : pip install watchdog")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Chemins

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
ASSEMBLED     = WORKSPACE_DIR / "10_output" / "bulletin_complet_publication.md"
CSS_FILE      = SCRIPT_DIR / "preview.css"
ASSEMBLER     = SCRIPT_DIR / "assembler_markdown.py"
REGIME_VISUALIZER = SCRIPT_DIR / "visualiser_regimes.py"
REGIME_DASHBOARD  = WORKSPACE_DIR / "10_output" / "dashboard_regimes.html"
REGIME_DB_FILE          = WORKSPACE_DIR / "06_donnees" / "protection_sociale_rdc.db"
DASHBOARD_SETTINGS_FILE   = WORKSPACE_DIR / "10_output" / "dashboard_settings.json"
QUESTIONNAIRE_DATA_FILE   = WORKSPACE_DIR / "10_output" / "questionnaire_data.json"
PRESTATION_SETTINGS_FILE  = WORKSPACE_DIR / "10_output" / "prestation_settings.json"
DENOMINATEURS_DB_FILE     = WORKSPACE_DIR / "protection_sociale_rdc.db"
PORT          = 8765

# ---------------------------------------------------------------------------
# Cache partagé

_html_cache = "<p><em>Chargement en cours…</em></p>"
_html_lock  = threading.Lock()
_rebuild_lock = threading.Lock()
_clients    = []
_clients_lock = threading.Lock()
_word_export_lock = threading.Lock()
_word_export_state = {
    "status": "idle",
    "error": "",
    "filename": "",
}
_text_edit_lock = threading.Lock()

TEXT_EDIT_SOURCE_DIRS = {
    "01_pages_preliminaires",
    "02_introduction_generale",
    "03_chapitres",
    "04_annexes",
}
TEXT_EDIT_MAX_BODY_BYTES = 2 * 1024 * 1024
MANUAL_EDIT_START = "<!-- MANUEL_EDIT:DEBUT -->"
MANUAL_EDIT_END = "<!-- MANUEL_EDIT:FIN -->"
TABLE_TOKEN_RE = re.compile(r"\[\[TABLEAU_LECTURE_SEULE_\d+_[0-9a-f]{10}\]\]")


def notify_clients():
    """Envoie un signal de rechargement à tous les navigateurs connectés."""
    with _clients_lock:
        for q in _clients:
            try:
                q.put_nowait("reload")
            except queue.Full:
                pass


def run_assembler(preview_path):
    """Relance l'assembleur Markdown. Retourne True si succès."""
    result = subprocess.run(
        [sys.executable, str(ASSEMBLER), "--preview-markdown", str(preview_path)],
        capture_output=True,
        cwd=str(WORKSPACE_DIR),
        encoding="cp1252",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"[ASSEMBLEUR] Erreur :\n{result.stderr.strip()}")
        return False
    print("[ASSEMBLEUR] OK")
    return True


def run_regime_dashboard():
    """Régénère le tableau de bord des régimes si le générateur est disponible."""
    if not REGIME_VISUALIZER.exists():
        return False
    result = subprocess.run(
        [sys.executable, str(REGIME_VISUALIZER)],
        capture_output=True,
        cwd=str(WORKSPACE_DIR),
        encoding="cp1252",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"[DASHBOARD] Erreur :\n{result.stderr.strip()}")
        return False
    print("[DASHBOARD] OK")
    return True


def _dashboard_refresh_required(dashboard_path: pathlib.Path) -> bool:
    """Indique si le dashboard doit être régénéré avant d'être servi.

    Le dashboard dépend du script de génération et des bases SQLite
    (ESS + dénominateurs). Un import ESS peut modifier la base sans toucher
    le script ; dans ce cas il faut régénérer le HTML/JS.
    """
    if not dashboard_path.exists():
        return True
    try:
        dashboard_mtime = dashboard_path.stat().st_mtime
    except OSError:
        return True

    dependencies = [REGIME_VISUALIZER, REGIME_DB_FILE, DENOMINATEURS_DB_FILE]
    for dep in dependencies:
        try:
            if dep.exists() and dep.stat().st_mtime > dashboard_mtime:
                return True
        except OSError:
            continue
    return False


# ---------------------------------------------------------------------------
# Indicateurs de statut — code couleur validation

STATUS_CLASSES = {
    'brouillon': ('status-brouillon', 'Brouillon'),
    'à revoir':  ('status-arevoir',   'À revoir'),
    'revu':      ('status-revu',      'Revu'),
    'validé':    ('status-valide',    'Validé'),
}


def build_status_map(md_text: str) -> dict:
    """Construit {texte_titre: (css_class, label)} en lisant les NOTE_INTERNE.

    Gère deux formats :
      Statut : brouillon      (valeur sur la même ligne)
      Statut :                (valeur sur la ligne suivante)
      à revoir
    """
    mapping = {}
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        m = re.match(r'^#{1,6}\s+(.+)$', lines[i])
        if m:
            heading_text = m.group(1).strip()
            statut = None
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
                    raw = re.sub(r'\s*-->.*$', '', raw).strip()
                    raw = re.sub(r'[\[\]]', '', raw).strip()
                    if '|' in raw or raw == '':
                        # Valeur sur la ligne suivante
                        if j + 1 < len(lines):
                            nxt = lines[j + 1].strip()
                            nxt = re.sub(r'\s*-->.*$', '', nxt).strip()
                            if nxt and '|' not in nxt:
                                raw = nxt
                    if raw and '|' not in raw:
                        statut = raw.lower()
                    break
            if statut and statut in STATUS_CLASSES:
                mapping[heading_text] = STATUS_CLASSES[statut]
        i += 1
    return mapping


def inject_status_dots_html(html: str, status_map: dict) -> str:
    """Injecte un point coloré dans les balises de titre HTML correspondantes."""
    for heading_text, (cls, label) in status_map.items():
        dot = (f'<span class="status-dot {cls}" title="{label}">&#9679;</span> ')
        pattern = r'(<h[1-6][^>]*>)(' + re.escape(heading_text) + r')(</h[1-6]>)'
        html = re.sub(
            pattern,
            lambda mo: mo.group(1) + dot + mo.group(2) + mo.group(3),
            html,
        )
    return html


def preprocess_md(md_text: str) -> str:
    """Prépare le markdown pour la prévisualisation :
    - Supprime le H1 initial (titre du document) — déjà affiché dans la topbar
    - Supprime les titres '## Texte rédigé' (conserve le contenu dessous)
    - Ne fabrique pas de marqueur pour les sections sans texte
    - Supprime les blocs NOTE_INTERNE (<!-- NOTE_INTERNE ... -->)
    """
    # 1. Supprimer les blocs NOTE_INTERNE
    md_text = re.sub(r'<!--\s*NOTE_INTERNE.*?-->', '', md_text, flags=re.DOTALL)
    md_text = re.sub(
        r'<span\b[^>]*class="[^"]*\bvalid-badge\b[^"]*"[^>]*>.*?</span>',
        '',
        md_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    md_text = re.sub(
        r'<a\b[^>]*>\s*\[src\]\s*</a>',
        '',
        md_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    md_text = re.sub(r'(?im)(?<!\w)\[src\](?!\w)', '', md_text)
    md_text = re.sub(
        r'(?im)^\s*(?:[*_]\s*)?\[(?:à rédiger|à définir|à compléter)(?:[^\]]*)\]'
        r'(?:\s*[*_])?\s*$',
        '',
        md_text,
    )

    # 2. Supprimer les commentaires de version (<!-- VERSION ... --> et <!-- Généré ... -->)
    md_text = re.sub(r'<!--[^>]*-->', '', md_text)

    # 3. Supprimer le premier H1 du document (titre du projet, déjà dans la topbar)
    md_text = re.sub(r'^\s*#\s+.+\n', '', md_text, count=1)

    # 4. Traiter les titres "## Texte rédigé"
    lines = md_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^##\s+Texte\s+r[eé]dig[eé]\s*$', line, re.IGNORECASE):
            # Collecter le contenu jusqu'au prochain h1/h2
            i += 1
            content_lines = []
            while i < len(lines):
                if re.match(r'^#{1,2}\s+', lines[i]):
                    break
                content_lines.append(lines[i])
                i += 1
            # Vérifier si le contenu est vide ou placeholder
            content = '\n'.join(content_lines).strip()
            content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL).strip()
            is_empty = (
                not content_no_comments
                or len(content_no_comments) < 15
                or re.match(r'^[\[_*].*?(rédiger|à compléter|en cours).*?[\]_*]$',
                            content_no_comments, re.IGNORECASE)
            )
            if is_empty:
                pass
            else:
                result.extend(content_lines)
            continue
        result.append(line)
        i += 1
    return '\n'.join(result)
    lines = md_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^##\s+Texte\s+r[eé]dig[eé]\s*$', line, re.IGNORECASE):
            # Collecter le contenu jusqu'au prochain h1/h2
            i += 1
            content_lines = []
            while i < len(lines):
                if re.match(r'^#{1,2}\s+', lines[i]):
                    break
                content_lines.append(lines[i])
                i += 1
            # Vérifier si le contenu est vide ou placeholder
            content = '\n'.join(content_lines).strip()
            content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL).strip()
            is_empty = (
                not content_no_comments
                or len(content_no_comments) < 15
                or re.match(r'^[\[_*].*?(rédiger|à compléter|en cours).*?[\]_*]$',
                            content_no_comments, re.IGNORECASE)
            )
            if is_empty:
                result.append('\n<p class="a-rediger">&#9998; Texte à rédiger</p>\n')
            else:
                result.extend(content_lines)
            continue
        result.append(line)
        i += 1
    return '\n'.join(result)


def enrich_source_refs(html: str, md_text: str) -> str:
    """Pour chaque <a class="source-ref"> sans data-val-id,
    génère un id stable à partir du href et injecte data-val-id + data-val-file.
    Le val-file est déduit du fichier source Markdown via le href du lien.
    """
    import hashlib

    # Construire un mapping href -> fichier source MD
    # En cherchant chaque href dans les fichiers assemblés
    # On lit le build_config pour retrouver quel fichier contient chaque href
    href_to_file = {}
    try:
        import yaml
        cfg_path = WORKSPACE_DIR / "build_config.yml"
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8-sig"))
            for section in cfg.get("sections", []):
                for f in section.get("files", []):
                    fpath = WORKSPACE_DIR / f
                    if fpath.exists():
                        content = fpath.read_text(encoding="utf-8-sig")
                        for href in re.findall(r'href="(/files/[^"]+)"', content):
                            href_to_file.setdefault(href, f)
    except Exception:
        pass

    def add_val_attrs(m):
        tag = m.group(0)
        # Déjà enrichi
        if 'data-val-id' in tag:
            return tag
        # Extraire href
        href_m = re.search(r'href="([^"]+)"', tag)
        if not href_m:
            return tag
        href = href_m.group(1).split("?")[0]  # sans query string
        # Générer un id stable court
        val_id = "src-" + hashlib.md5(href.encode()).hexdigest()[:8]
        # Fichier source
        val_file = href_to_file.get(href, "")
        # Injecter avant la fermeture de la balise ouvrante
        inject = f' data-val-id="{val_id}" data-val-file="{val_file}" data-val-status="brouillon"'
        return tag[:-1] + inject + ">"

    return re.sub(r'<a\b[^>]*class="[^"]*source-ref[^"]*"[^>]*>', add_val_attrs, html)


def _split_text_edit_section(md_text: str):
    """Isole le corps public complet, avec ou sans rubrique Texte rédigé."""
    visible_text = re.sub(
        r"<!--.*?-->",
        lambda match: re.sub(r"[^\r\n]", " ", match.group()),
        md_text,
        flags=re.S,
    )
    headings = list(re.finditer(
        r"(?im)^##[ \t]+Texte[ \t]+r[eé]dig[eé][ \t]*(?:\r?\n|\Z)",
        visible_text,
    ))
    if not headings:
        heading = re.match(r"\s*#{1,2}[ \t]+[^\r\n]*(?:\r?\n|\Z)", md_text)
        if heading is None:
            return None
        body_start = heading.end()
        leading_notes = re.match(
            r"(?:\s+|<!--(?!\s*MANUEL_EDIT:).*?-->)*", md_text[body_start:], re.S
        )
        body_start += leading_notes.end()
    elif len(headings) != 1:
        raise ValueError("Le fichier doit contenir une seule section « Texte rédigé ».")
    else:
        body_start = headings[0].end()

    return md_text[:body_start], md_text[body_start:], ""


def _unwrap_manual_edit(body: str) -> str:
    has_start = MANUAL_EDIT_START in body
    has_end = MANUAL_EDIT_END in body
    if not has_start and not has_end:
        return body
    if (
        body.count(MANUAL_EDIT_START) != 1
        or body.count(MANUAL_EDIT_END) != 1
    ):
        raise ValueError("Les marqueurs de modification manuelle sont invalides.")

    start = body.index(MANUAL_EDIT_START)
    end = body.index(MANUAL_EDIT_END)
    if end <= start:
        raise ValueError("Les marqueurs de modification manuelle sont dans le désordre.")
    content = body[start + len(MANUAL_EDIT_START):end]
    before, after = body[:start], body[end + len(MANUAL_EDIT_END):]
    if before.strip() or after.strip():
        # Une ancienne modification peut ne couvrir qu'une sous-section.
        return before + content + after
    return content.strip("\r\n")


def _is_pipe_table_separator(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in cells
    )


def _readonly_table_spans(body: str):
    spans = [
        (match.start(), match.end())
        for match in re.finditer(r"<table\b.*?</table\s*>", body, re.I | re.S)
    ]

    lines = body.splitlines(keepends=True)
    offsets = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)

    index = 1
    while index < len(lines):
        if not _is_pipe_table_separator(lines[index]) or "|" not in lines[index - 1]:
            index += 1
            continue
        start_line = index - 1
        end_line = index + 1
        while end_line < len(lines) and "|" in lines[end_line]:
            end_line += 1
        spans.append((
            offsets[start_line],
            offsets[end_line] if end_line < len(lines) else len(body),
        ))
        index = end_line

    return sorted(spans)


def _mask_readonly_tables(body: str):
    """Remplace les tableaux par des repères vérifiés avant toute sauvegarde."""
    spans = _readonly_table_spans(body)
    masked_parts = []
    tables = []
    cursor = 0
    for start, end in spans:
        if start < cursor:
            continue
        table = body[start:end]
        token = (
            f"[[TABLEAU_LECTURE_SEULE_{len(tables) + 1}_"
            f"{hashlib.sha256(table.encode('utf-8')).hexdigest()[:10]}]]"
        )
        if token in body:
            raise ValueError("Un repère de tableau réservé apparaît déjà dans le texte.")
        masked_parts.append(body[cursor:start])
        masked_parts.append(token)
        if table.endswith("\r\n"):
            masked_parts.append("\r\n")
        elif table.endswith("\n"):
            masked_parts.append("\n")
        tables.append((token, table))
        cursor = end
    masked_parts.append(body[cursor:])
    return "".join(masked_parts), tables


def _restore_readonly_tables(edited_body: str, tables):
    expected_tokens = [token for token, _ in tables]
    found_tokens = TABLE_TOKEN_RE.findall(edited_body)
    if found_tokens != expected_tokens:
        raise ValueError(
            "Les repères des tableaux en lecture seule doivent rester inchangés et dans le même ordre."
        )

    restored = edited_body
    for token, table in tables:
        newline = "\r\n" if table.endswith("\r\n") else "\n" if table.endswith("\n") else ""
        placeholder = token + newline if newline and token + newline in restored else token
        restored = restored.replace(placeholder, table, 1)
    return restored


def _text_edit_sources(only_file=None):
    """Charge les seules sources éditables déclarées dans la configuration."""
    import yaml

    config_path = WORKSPACE_DIR / "build_config.yml"
    try:
        with config_path.open(encoding="utf-8-sig") as config_file:
            config = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        raise ValueError(f"Lecture de build_config.yml impossible : {exc}") from exc
    if not isinstance(config, dict) or not isinstance(config.get("sections"), list):
        raise ValueError("La configuration des sections est invalide.")

    root = WORKSPACE_DIR.resolve()
    sources = {}
    for section in config["sections"]:
        if not isinstance(section, dict):
            continue
        configured_files = section.get("files", [])
        if not isinstance(configured_files, list):
            raise ValueError("La liste des fichiers d'une section est invalide.")
        for configured_path in configured_files:
            if not isinstance(configured_path, str) or not configured_path.lower().endswith(".md"):
                continue
            normalized = configured_path.replace("\\", "/")
            if only_file is not None and normalized != only_file:
                continue
            relative = pathlib.PurePosixPath(normalized)
            if (
                relative.is_absolute()
                or not relative.parts
                or relative.parts[0] not in TEXT_EDIT_SOURCE_DIRS
                or ".." in relative.parts
            ):
                continue
            target = (root / pathlib.Path(*relative.parts)).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                continue
            if not target.is_file():
                continue

            raw_bytes = target.read_bytes()
            md_text = raw_bytes.decode("utf-8-sig")
            section_parts = _split_text_edit_section(md_text)
            if section_parts is None:
                continue
            prefix, raw_body, suffix = section_parts
            editable_body = _unwrap_manual_edit(raw_body)
            masked_body, tables = _mask_readonly_tables(editable_body)
            if not re.sub(r"<!--.*?-->", "", editable_body, flags=re.S).strip():
                continue

            title_match = re.search(r"(?m)^#{1,2}\s+(.+?)\s*$", md_text)
            title = title_match.group(1).strip() if title_match else relative.stem
            title = re.sub(r"<[^>]*>", "", title).strip()
            sources[normalized] = {
                "file": normalized,
                "title": title,
                "target": target,
                "raw_bytes": raw_bytes,
                "revision": hashlib.sha256(raw_bytes).hexdigest(),
                "prefix": prefix,
                "body": raw_body,
                "suffix": suffix,
                "content": masked_body.replace("\r\n", "\n").replace("\r", "\n"),
                "tables": tables,
            }
    return sources


def _render_manual_edit_markers(md_text: str) -> str:
    return md_text.replace(
        MANUAL_EDIT_START,
        '<div class="manual-edit" markdown="1">',
    ).replace(MANUAL_EDIT_END, "</div>")


class _VisualTextSourceParser(HTMLParser):
    """Repère les caractères de texte sans exposer les attributs HTML."""

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.ranges = []
        self.lines = [0]
        for match in re.finditer("\n", source):
            self.lines.append(match.end())

    def handle_data(self, data):
        line, column = self.getpos()
        start = self.lines[line - 1] + column
        self.ranges.append((start, start + len(data)))

    def handle_entityref(self, name):
        self.handle_data("&" + name + ";")

    def handle_charref(self, name):
        self.handle_data("&#" + name + ";")


class _VisualTextRenderer(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        parser = _VisualTextSourceParser(source)
        parser.feed(source)
        self.ranges = []
        for start, end in parser.ranges:
            if self.ranges and self.ranges[-1][1] == start:
                self.ranges[-1] = (self.ranges[-1][0], end)
            else:
                self.ranges.append((start, end))
        self.cursor = 0
        self.stack = []
        self.weights = []
        self.output = []
        self.slots = {}
        self.generated = False

    def handle_comment(self, data):
        marker = re.fullmatch(r"\s*AUTO_GENERE:[^:\s]+:(DEBUT|FIN)\s*", data)
        if marker:
            self.generated = marker.group(1) == "DEBUT"

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        locked = (
            tag in {"table", "pre", "code", "script", "style", "svg"}
            or "valid-badge" in attributes.get("class", "").split()
            or "table-caption" in attributes.get("class", "").split()
            or any(self.stack)
        )
        if tag not in {"img", "br", "hr", "input", "meta", "link", "wbr"}:
            self.stack.append(locked)
            bold = bool(self.weights and self.weights[-1])
            if tag in {"strong", "b", "h1", "h2", "h3", "h4", "h5", "h6"}:
                bold = True
            elif attributes.get("style") == "font-weight: normal":
                bold = False
            self.weights.append(bold)
        self.output.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()
            self.weights.pop()
        self.output.append(f"</{tag}>")

    def handle_data(self, text):
        escaped = html_lib.escape(text, quote=False)
        if not text.strip():
            self.output.append(escaped)
            return
        candidates = []
        for range_start, range_end in self.ranges:
            if range_end <= self.cursor:
                continue
            start = max(range_start, self.cursor)
            decoded = []
            offsets = []
            for match in re.finditer(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z]\w*);|\r\n?|.", self.source[start:range_end], re.S):
                value = html_lib.unescape(match.group())
                # Markdown normalise les retours, mais les offsets restent ceux du fichier.
                value = value.replace("\r\n", "\n").replace("\r", "\n")
                decoded.append(value)
                offsets.extend([(start + match.start(), start + match.end())] * len(value))
            found = "".join(decoded).find(text)
            if found >= 0:
                candidates.append((offsets[found][0], offsets[found + len(text) - 1][1]))
                break
        if not candidates:
            self.output.append(escaped)
            return
        start, end = min(candidates)
        self.cursor = end
        if any(self.stack) or self.generated:
            self.output.append(escaped)
            return
        slot_id = str(len(self.slots))
        display_text = re.sub(r"\r\n?|\n", " ", text)
        bold = bool(self.weights and self.weights[-1])
        self.slots[slot_id] = {"start": start, "end": end, "text": display_text,
                               "bold": bold, "parent_bold": any(self.weights[-2:-1])}
        self.output.append(
            f'<span data-text-slot="{slot_id}" contenteditable="plaintext-only"'
            f' data-bold="{int(bold)}" role="textbox" aria-label="Passage de texte">'
            f'{html_lib.escape(display_text, quote=False)}</span>'
        )


def _visual_text_document(source):
    body = _unwrap_manual_edit(source["body"])
    rendered = markdown.markdown(body, extensions=["tables", "fenced_code", "md_in_html"])
    renderer = _VisualTextRenderer(body)
    renderer.feed(rendered)
    return {"html": "".join(renderer.output), "slots": renderer.slots, "body": body}


def _escape_visual_text(text):
    if not isinstance(text, str) or "\n" in text or "\r" in text:
        raise ValueError("Le passage doit contenir du texte sur une seule ligne.")
    return re.sub(r"[\\`*_{}\[\]()#+.!|>~-]", lambda m: f"&#{ord(m.group())};",
                  html_lib.escape(text, quote=False))


def _apply_visual_text_changes(source, changes):
    document = _visual_text_document(source)
    if not isinstance(changes, dict) or not changes:
        raise ValueError("Aucune modification de texte à enregistrer.")
    replacements = []
    body = document["body"]
    for slot_id, text in changes.items():
        slot = document["slots"].get(slot_id)
        if slot is None:
            raise ValueError("Passage de texte inconnu ou contenu invalide.")
        start, end = slot["start"], slot["end"]
        if isinstance(text, str):
            if text != slot["text"]:
                replacements.append((start, end, _escape_visual_text(text)))
            continue
        if not isinstance(text, list) or not text:
            raise ValueError("Mise en forme de texte invalide.")
        inherited = slot["bold"]
        # Retirer une enveloppe simple, sans toucher aux liens ni aux annotations.
        for left, right, weight in (("**", "**", True), ("__", "__", True),
                                    ("<strong>", "</strong>", True), ("<b>", "</b>", True),
                                    ('<span style="font-weight: normal">', "</span>", False)):
            if (weight == inherited and body[:start].endswith(left)
                    and body.startswith(right, end)):
                start -= len(left)
                end += len(right)
                inherited = slot["parent_bold"]
                break
        parts = []
        for run in text:
            if not isinstance(run, dict) or type(run.get("bold")) is not bool:
                raise ValueError("Mise en forme de texte invalide.")
            value = _escape_visual_text(run.get("text"))
            if run["bold"] != inherited:
                value = (f"<strong>{value}</strong>" if run["bold"] else
                         f'<span style="font-weight: normal">{value}</span>')
            parts.append(value)
        replacements.append((start, end, "".join(parts)))
    for start, end, text in sorted(replacements, reverse=True):
        body = body[:start] + text + body[end:]
    masked, _ = _mask_readonly_tables(body)
    return masked


def _build_text_edit_update(source: dict, edited_body: str) -> bytes:
    restored_body = _restore_readonly_tables(edited_body, source["tables"])
    if not TABLE_TOKEN_RE.sub("", edited_body).strip():
        raise ValueError("Le texte rédigé ne peut pas être vide.")

    newline = "\r\n" if "\r\n" in source["body"] else "\n"
    restored_body = restored_body.replace("\r\n", "\n").replace("\r", "\n")
    restored_body = restored_body.strip("\n").replace("\n", newline)
    wrapped_body = (
        newline
        + MANUAL_EDIT_START + newline
        + restored_body + newline
        + MANUAL_EDIT_END + newline + newline
    )
    updated_text = source["prefix"] + wrapped_body + source["suffix"]
    has_utf8_bom = source["raw_bytes"].startswith(b"\xef\xbb\xbf")
    return (
        (b"\xef\xbb\xbf" if has_utf8_bom else b"")
        + updated_text.encode("utf-8")
    )


TEXT_EDIT_BUTTON = """
    <button id="text-edit-open" class="topbar-btn" type="button">
      ✏️ Modifier le texte
    </button>
"""

TEXT_EDIT_MODAL = """
<div id="text-edit-dialog" class="text-edit-dialog" hidden>
  <div class="text-edit-backdrop" data-text-edit-close></div>
  <section class="text-edit-panel" role="dialog" aria-modal="true"
           aria-labelledby="text-edit-title">
    <header class="text-edit-header">
      <div>
        <h2 id="text-edit-title">Modifier le texte du bulletin</h2>
        <p>La sauvegarde modifie uniquement le texte public de la section choisie. Les notes internes sont préservées et les tableaux restent en lecture seule.</p>
      </div>
      <button id="text-edit-x" class="text-edit-close" type="button" aria-label="Fermer">×</button>
    </header>
    <label class="text-edit-label" for="text-edit-file">Rubrique du sommaire</label>
    <select id="text-edit-file" disabled>
      <option>Chargement des sections…</option>
    </select>
    <div id="text-edit-path" class="text-edit-path"></div>
    <div><button id="text-edit-bold" type="button" aria-pressed="false" disabled><strong>Gras</strong></button></div>
    <div id="text-edit-content" spellcheck="true" aria-label="Texte rédigé" aria-busy="true"></div>
    <p class="text-edit-help">Sélectionnez du texte dans un passage, puis cliquez sur « Gras » pour appliquer ou retirer le gras (Ctrl+B ou ⌘B). Les tableaux et les blocs générés automatiquement sont verrouillés.</p>
    <div id="text-edit-status" class="text-edit-status" role="status" aria-live="polite"></div>
    <footer class="text-edit-actions">
      <button id="text-edit-cancel" class="text-edit-secondary" type="button">Fermer</button>
      <button id="text-edit-save" class="text-edit-primary" type="button" disabled>Enregistrer</button>
    </footer>
  </section>
</div>
"""

TEXT_EDIT_SCRIPT = r"""
<script>
(function() {
  const openButton = document.getElementById("text-edit-open");
  const dialog = document.getElementById("text-edit-dialog");
  const select = document.getElementById("text-edit-file");
  const editor = document.getElementById("text-edit-content");
  const boldButton = document.getElementById("text-edit-bold");
  const pathLabel = document.getElementById("text-edit-path");
  const status = document.getElementById("text-edit-status");
  const saveButton = document.getElementById("text-edit-save");
  const cancelButton = document.getElementById("text-edit-cancel");
  const closeButton = document.getElementById("text-edit-x");
  if (!openButton || !dialog || !select || !editor || !saveButton) return;

  let currentFile = "";
  let currentRevision = "";
  let originalContent = {};
  let loading = false;
  let selectedEntry = "";
  const sections = new Map();
  let sourceFile = "";
  document.querySelectorAll("#content [data-preview-file], #content :is(h1,h2,h3)[id]").forEach(node => {
    if (node.hasAttribute("data-preview-file")) sourceFile = node.dataset.previewFile;
    else if (sourceFile) sections.set(node.id, {file: sourceFile, heading: node});
  });

  function headingLabel(heading) {
    const copy = heading.cloneNode(true);
    copy.querySelectorAll(".valid-badge, .toc-toggle").forEach(node => node.remove());
    return copy.textContent.replace(/\s+/g, " ").trim();
  }

  function showPassage(entry) {
    editor.scrollTop = 0;
    if (!entry) return;
    const label = headingLabel(entry.heading);
    const matches = Array.from(editor.querySelectorAll(entry.heading.tagName))
      .filter(node => headingLabel(node) === label);
    const similar = Array.from(sections.values()).filter(other =>
      other.file === entry.file && other.heading.tagName === entry.heading.tagName &&
      headingLabel(other.heading) === label);
    const target = matches[similar.indexOf(entry)];
    if (target) editor.scrollTop += target.getBoundingClientRect().top - editor.getBoundingClientRect().top - 10;
  }

  function isBold(node) {
    return node.parentElement.closest("[data-bold]").dataset.bold === "1";
  }

  function slotValue(slot) {
    if (!slot.querySelector("[data-bold]")) return slot.textContent;
    const runs = [];
    const walker = document.createTreeWalker(slot, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.length) continue;
      const bold = isBold(node);
      const last = runs[runs.length - 1];
      if (last && last.bold === bold) last.text += node.data;
      else runs.push({text: node.data, bold});
    }
    return runs.some(run => run.bold !== (slot.dataset.bold === "1")) ? runs : slot.textContent;
  }

  function selectionInfo() {
    const selection = window.getSelection();
    if (loading || dialog.hidden || !selection.rangeCount || selection.isCollapsed) return null;
    const range = selection.getRangeAt(0);
    const root = range.commonAncestorContainer;
    const slot = (root.parentElement && (root.nodeType === 1 ? root : root.parentElement))
      ?.closest("[data-text-slot]");
    if (!slot || !editor.contains(slot)) return null;
    const walker = document.createTreeWalker(slot, NodeFilter.SHOW_TEXT);
    let bold = true;
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (range.intersectsNode(node) && !(node === range.startContainer && range.startOffset === node.length)
          && !(node === range.endContainer && range.endOffset === 0)) bold = bold && isBold(node);
    }
    return range.toString() ? {range, bold} : null;
  }

  function updateBoldState() {
    const info = selectionInfo();
    boldButton.disabled = !info;
    boldButton.setAttribute("aria-pressed", String(Boolean(info && info.bold)));
  }

  function toggleBold() {
    const info = selectionInfo();
    if (!info) return;
    const span = document.createElement("span");
    span.dataset.bold = info.bold ? "0" : "1";
    span.style.fontWeight = info.bold ? "normal" : "bold";
    span.textContent = info.range.toString();
    info.range.deleteContents();
    info.range.insertNode(span);
    info.range.selectNodeContents(span);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(info.range);
    updateBoldState();
    updateSaveState();
  }

  boldButton.addEventListener("mousedown", event => event.preventDefault());
  boldButton.addEventListener("click", toggleBold);
  document.addEventListener("selectionchange", updateBoldState);
  editor.addEventListener("keydown", function(event) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "b") {
      event.preventDefault();
      toggleBold();
    }
  });

  function changes() {
    const result = {};
    editor.querySelectorAll("[data-text-slot]").forEach(function(element) {
      const id = element.dataset.textSlot;
      const value = slotValue(element);
      if (JSON.stringify(value) !== originalContent[id]) result[id] = value;
    });
    return result;
  }

  function setLoading(value) {
    loading = value;
    editor.inert = value;
    editor.setAttribute("aria-busy", String(value));
    select.disabled = value;
    cancelButton.disabled = value;
    closeButton.disabled = value;
    updateBoldState();
    updateSaveState();
  }

  async function requestJson(url, options) {
    const response = await fetch(url, Object.assign({cache: "no-store"}, options || {}));
    let payload;
    try {
      payload = await response.json();
    } catch (error) {
      throw new Error("Réponse serveur illisible.");
    }
    if (!response.ok) throw new Error(payload.error || "La requête a échoué.");
    return payload;
  }

  function setStatus(message, isError) {
    status.textContent = message || "";
    status.classList.toggle("error", Boolean(isError));
  }

  function updateSaveState() {
    const pending = changes();
    editor.querySelectorAll("[data-text-slot]").forEach(function(element) {
      element.classList.toggle(
        "text-edit-changed",
        Object.hasOwn(pending, element.dataset.textSlot)
      );
    });
    saveButton.disabled = loading || !currentFile || Object.keys(pending).length === 0;
  }

  async function loadFile(key) {
    selectedEntry = key;
    const entry = sections.get(key);
    const file = entry ? entry.file : key;
    setLoading(true);
    setStatus("Chargement…", false);
    try {
      const payload = await requestJson("/api/text-edit?file=" + encodeURIComponent(file));
      currentFile = payload.file;
      currentRevision = payload.revision;
      originalContent = {};
      editor.innerHTML = payload.html;
      editor.querySelectorAll("[data-text-slot]").forEach(function(element) {
        originalContent[element.dataset.textSlot] = JSON.stringify(slotValue(element));
      });
      pathLabel.textContent = payload.file;
      setStatus(
        Object.keys(originalContent).length
          ? ""
          : "Cette section ne contient aucun passage de texte modifiable. Les tableaux et les éléments protégés restent en lecture seule.",
        false
      );
      showPassage(entry);
    } catch (error) {
      currentFile = "";
      currentRevision = "";
      editor.innerHTML = "";
      pathLabel.textContent = file;
      setStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  }

  async function openEditor() {
    dialog.hidden = false;
    openButton.disabled = true;
    setLoading(true);
    setStatus("Chargement des sections…", false);
    try {
      if (sections.size) {
        select.replaceChildren();
        let current = "";
        const top = document.getElementById("main").getBoundingClientRect().top;
        const anchor = document.querySelector("#content :target");
        document.querySelectorAll("#sidebar .toc a[href^='#']").forEach(link => {
          const id = decodeURIComponent(link.hash.slice(1));
          const entry = sections.get(id);
          if (!entry) return;
          const h = entry.heading;
          select.add(new Option("\u00a0\u00a0".repeat(Number(h.tagName.slice(1)) - 1) + headingLabel(h), id));
          if (h.getBoundingClientRect().top <= top + 80) current = id;
        });
        if (anchor && sections.has(anchor.id) && anchor.getBoundingClientRect().bottom >= top &&
            anchor.getBoundingClientRect().top < window.innerHeight) current = anchor.id;
        if (current) select.value = current;
        await loadFile(select.value);
        return;
      }
      const payload = await requestJson("/api/text-edit/files");
      select.innerHTML = "";
      payload.files.forEach(function(file) {
        const option = document.createElement("option");
        option.value = file.file;
        option.textContent = file.title;
        select.appendChild(option);
      });
      if (!payload.files.length) {
        setStatus("Aucune section contenant du texte public n’est disponible.", true);
        return;
      }
      select.disabled = false;
      await loadFile(payload.files[0].file);
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      openButton.disabled = false;
      setLoading(false);
    }
  }

  function closeEditor() {
    if (loading) return;
    if (Object.keys(changes()).length &&
        !window.confirm("Les modifications non enregistrées seront perdues. Fermer ?")) return;
    dialog.hidden = true;
    if (dialog.dataset.pendingReload) window.location.reload();
  }

  openButton.addEventListener("click", openEditor);
  cancelButton.addEventListener("click", closeEditor);
  closeButton.addEventListener("click", closeEditor);
  dialog.querySelector("[data-text-edit-close]").addEventListener("click", closeEditor);
  select.addEventListener("change", function() {
    const entry = sections.get(select.value);
    if (entry && entry.file === currentFile) {
      selectedEntry = select.value;
      showPassage(entry);
      return;
    }
    if (Object.keys(changes()).length &&
        !window.confirm("Abandonner les modifications non enregistrées ?")) {
      select.value = selectedEntry;
      return;
    }
    loadFile(select.value);
  });
  editor.addEventListener("input", updateSaveState);
  editor.addEventListener("click", function(event) {
    if (event.target.closest("a")) event.preventDefault();
  });
  editor.addEventListener("beforeinput", function(event) {
    if (event.inputType === "insertParagraph" || event.inputType === "insertLineBreak") {
      event.preventDefault();
    }
  });
  window.addEventListener("beforeunload", function(event) {
    if (!dialog.hidden && Object.keys(changes()).length) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  document.addEventListener("keydown", function(event) {
    if (event.key === "Escape" && !dialog.hidden) closeEditor();
  });

  saveButton.addEventListener("click", async function() {
    if (saveButton.disabled) return;
    setLoading(true);
    setStatus("Enregistrement et mise à jour du bulletin…", false);
    try {
      await requestJson("/api/text-edit/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          file: currentFile,
          revision: currentRevision,
          changes: changes()
        })
      });
      editor.querySelectorAll("[data-text-slot]").forEach(function(element) {
        originalContent[element.dataset.textSlot] = JSON.stringify(slotValue(element));
      });
      setStatus("Enregistré. Rechargement de la prévisualisation…", false);
      if (sections.has(selectedEntry)) {
        history.replaceState(null, "", "#" + encodeURIComponent(selectedEntry));
      }
      window.location.reload();
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      setLoading(false);
    }
  });
})();
</script>
"""


def build_html(preview_path=None) -> str:
    """Convertit le fichier assemblé en page HTML complète."""
    css = CSS_FILE.read_text(encoding="utf-8-sig") if CSS_FILE.exists() else ""

    assembled = preview_path or ASSEMBLED
    if not assembled.exists():
        md_text = (
            "# Fichier introuvable\n\n"
            "_Le fichier `10_output/bulletin_complet_publication.md` n'existe pas encore._\n\n"
            "Vérifiez que `build_config.yml` est correct et relancez l'assembleur."
        )
    else:
        md_text = assembled.read_text(encoding="utf-8")

    status_map = {}
    md_preview = preprocess_md(_render_manual_edit_markers(md_text))
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "md_in_html",
            TocExtension(title="", toc_depth=3),
        ]
    )
    body = md.convert(md_preview)
    toc  = md.toc  # HTML généré par l'extension toc
    body = inject_status_dots_html(body, status_map)
    body = enrich_source_refs(body, md_text)
    # Envelopper chaque <table> dans un div scrollable
    body = re.sub(r'(<table)', r'<div class="table-scroll">\1', body)
    body = re.sub(r'(</table>)', r'\1</div>', body)

    # Horodatage de la dernière mise à jour
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bulletin statistique RDC 2026 — Prévisualisation</title>
  <style>{css}</style>
</head>
<body class="with-topbar">

<div id="topbar">
  <div id="topbar-info">
    PRÉVISUALISATION — Deuxième Bulletin statistique de la protection sociale en RDC
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Dernière mise à jour : {ts}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <span id="status">● En ligne</span>
  </div>
  <div id="topbar-actions">
    {TEXT_EDIT_BUTTON}
    <a href="/dashboard" target="_blank" class="topbar-btn topbar-link"
       title="Ouvrir le tableau de bord interactif des régimes (ESS)">
      📊 Tableau de bord
    </a>
    <div class="topbar-dropdown">
      <button class="topbar-btn topbar-dropdown-toggle" title="Options d'exportation">
        📤 Exporter ▾
      </button>
      <div class="topbar-dropdown-menu">
        <a href="/export" target="_blank" class="topbar-dropdown-item">
          🌐 HTML (relecture)
        </a>
        <a href="#" id="export-word-btn" class="topbar-dropdown-item"
           onclick="startWordExport(); return false;">
          📝 Word (.docx)
        </a>
        <a href="/download" class="topbar-dropdown-item">
          ⬇️ Télécharger HTML
        </a>
        <div class="topbar-dropdown-divider"></div>
        <a href="#" class="topbar-dropdown-item" onclick="exportPreviewPdf(); return false;">
          🖨️ PDF (impression)
        </a>
      </div>
    </div>
  </div>
</div>

<div id="sidebar">
  <div id="toc-header">Table des matières</div>
  {toc if toc else '<p style="padding:12px 18px;color:#667;font-size:12px;">Aucun titre détecté.</p>'}
</div>

<div id="main">
  <div id="content">
    {body}
  </div>
</div>

<div id="page-indicator">Page 1</div>
{TEXT_EDIT_MODAL}

<script>
/* ------------------------------------------------------------------ */
/* 1. Auto-refresh via Server-Sent Events                              */
/* ------------------------------------------------------------------ */
const evtSource = new EventSource("/events");
evtSource.onmessage = function(e) {{
  if (e.data !== "reload") return;
  const dialog = document.getElementById("text-edit-dialog");
  if (dialog && !dialog.hidden) dialog.dataset.pendingReload = "true";
  else window.location.reload();
}};
evtSource.onerror = function() {{
  const s = document.getElementById("status");
  if (s) {{ s.textContent = "● Déconnecté — relancer le serveur"; s.style.color = "#c00"; }}
}};

function exportPreviewPdf() {{
  const originalTitle = document.title;
  const now = new Date();
  const stamp = now.getFullYear()
    + "-" + String(now.getMonth() + 1).padStart(2, "0")
    + "-" + String(now.getDate()).padStart(2, "0");
  document.title = "bulletin_rdc_preview_" + stamp;
  window.print();
  setTimeout(function() {{ document.title = originalTitle; }}, 500);
}}

async function startWordExport() {{
  const button = document.getElementById("export-word-btn");
  if (!button || button.dataset.running === "true") return;
  button.dataset.running = "true";
  button.textContent = "⏳ Word — préparation…";

  try {{
    const startResponse = await fetch("/export-word/start", {{ cache: "no-store" }});
    const startData = await startResponse.json();
    if (!startResponse.ok) throw new Error(startData.error || "Impossible de lancer l’export Word.");

    while (true) {{
      await new Promise(function(resolve) {{ setTimeout(resolve, 1500); }});
      const statusResponse = await fetch("/export-word/status", {{ cache: "no-store" }});
      const statusData = await statusResponse.json();
      if (!statusResponse.ok) throw new Error(statusData.error || "État de l’export indisponible.");
      if (statusData.status === "done") {{
        button.textContent = "✅ Word — téléchargement";
        window.location.href = "/export-word/download";
        setTimeout(function() {{
          button.textContent = "📝 Word (.docx)";
          button.dataset.running = "false";
        }}, 2500);
        return;
      }}
      if (statusData.status === "error") {{
        throw new Error(statusData.error || "Échec de l’export Word.");
      }}
      button.textContent = "⏳ Word — export en cours…";
    }}
  }} catch (error) {{
    button.textContent = "❌ Word — échec";
    button.dataset.running = "false";
    alert(error.message);
  }}
}}

/* ------------------------------------------------------------------ */
/* 2. Sections repliables dans le contenu principal                    */
/*    Cliquer sur un titre replie/déplie tout son contenu.             */
/* ------------------------------------------------------------------ */
(function() {{
  function makeCollapsible(level) {{
    const content = document.getElementById("content");
    if (!content) return;
    Array.from(content.querySelectorAll("h" + level)).forEach(function(h) {{
      /* indicateur visuel */
      const tog = document.createElement("span");
      tog.className = "collapse-toggle";
      tog.innerHTML = "&#9660;";          /* ▼ */
      h.insertBefore(tog, h.firstChild);
      h.classList.add("collapsible-heading");

      /* collecter les éléments suivants jusqu'au prochain titre de niveau ≤ */
      const section = document.createElement("div");
      section.className = "collapsible-section";
      const toMove = [];
      let next = h.nextElementSibling;
      while (next) {{
        const tag = next.tagName || "";
        if (/^H[1-6]$/.test(tag) && parseInt(tag[1]) <= level) break;
        toMove.push(next);
        next = next.nextElementSibling;
      }}

      if (toMove.length > 0) {{
        h.parentNode.insertBefore(section, toMove[0]);
        toMove.forEach(function(el) {{ section.appendChild(el); }});
        h.addEventListener("click", function() {{
          const col = section.classList.toggle("collapsed");
          tog.innerHTML = col ? "&#9654;" : "&#9660;";  /* ▶ ou ▼ */
        }});
      }} else {{
        h.removeChild(tog);
        h.classList.remove("collapsible-heading");
      }}
    }});
  }}
  /* traiter du plus profond vers le plus haut pour respecter la hiérarchie */
  [4, 3, 2, 1].forEach(makeCollapsible);
}})();

/* ------------------------------------------------------------------ */
/* 3. TOC repliable dans la sidebar                                    */
/*    Cliquer sur la flèche replie/déplie les sous-entrées.            */
/* ------------------------------------------------------------------ */
(function() {{
  document.querySelectorAll("#sidebar .toc li").forEach(function(li) {{
    const sub  = li.querySelector(":scope > ul");
    if (!sub) return;
    const link = li.querySelector(":scope > a");
    if (!link) return;
    const tog = document.createElement("span");
    tog.className = "toc-toggle";
    tog.innerHTML = "&#9660;";           /* ▼ */
    link.insertBefore(tog, link.firstChild);
    tog.addEventListener("click", function(e) {{
      e.preventDefault();
      e.stopPropagation();
      const col = sub.classList.toggle("toc-collapsed");
      tog.innerHTML = col ? "&#9654;" : "&#9660;";
    }});
  }});
}})();

/* ------------------------------------------------------------------ */
/* 5. Numéro de page (simulé A4 ≈ 1123 px)                            */
/* ------------------------------------------------------------------ */
(function() {{
  const A4_PX   = 1123;   /* hauteur A4 à 96 dpi */
  const mainEl  = document.getElementById("main");
  const indic   = document.getElementById("page-indicator");
  if (!mainEl || !indic) return;

  function updatePage() {{
    const contentH = mainEl.scrollHeight;
    const total    = Math.max(1, Math.ceil(contentH / A4_PX));
    const current  = Math.min(total, Math.floor(mainEl.scrollTop / A4_PX) + 1);
    indic.textContent = "Page\u00a0" + current + "\u00a0/\u00a0" + total;
  }}

  mainEl.addEventListener("scroll", updatePage);
  updatePage();
}})();

/* ------------------------------------------------------------------ */
/* 4. Ancre active dans la sidebar au scroll                           */
/* ------------------------------------------------------------------ */
const allHeadings = document.querySelectorAll("h1[id], h2[id], h3[id]");
const tocLinks    = document.querySelectorAll("#sidebar .toc a");

function onScroll() {{
  let current = "";
  allHeadings.forEach(function(h) {{
    if (window.scrollY + 80 >= h.offsetTop) current = h.id;
  }});
  tocLinks.forEach(function(l) {{
    const active = l.getAttribute("href") === "#" + current;
    l.style.borderLeftColor = active ? "var(--couleur-accent)" : "transparent";
    l.style.color           = active ? "#fff" : "";
  }});
}}
document.getElementById("main").addEventListener("scroll", onScroll);

/* ------------------------------------------------------------------ */
/* 5. Tooltip flottant pour les annotations de source (.source-ref)   */
/* Délégation sur document pour survivre aux déplacements DOM         */
/* ------------------------------------------------------------------ */
(function() {{
  const tip = document.createElement("div");
  tip.id = "source-tooltip";
  tip.style.left = "-9999px";
  tip.style.top  = "-9999px";
  document.body.appendChild(tip);

  /* Ajouter target=_blank sur tous les liens source-ref
     et enrichir le href avec les paramètres de validation + contexte */
  document.querySelectorAll("a.source-ref").forEach(function(el) {{
    el.setAttribute("rel", "noopener noreferrer");
    const valId     = el.getAttribute("data-val-id");
    const valFile   = el.getAttribute("data-val-file");
    const valStatus = el.getAttribute("data-val-status") || "brouillon";

    /* Intercepter le clic pour enrichir l'URL avec contexte + val params */
    el.addEventListener("click", function(e) {{
      e.preventDefault();
      const href = (el.getAttribute("href") || "").split("?")[0];
      if (!href) return;

      /* Extraire la phrase complète du paragraphe parent */
      const para = el.closest("p, li, blockquote, td");
      const ctx     = para ? para.textContent.trim() : "";
      const anchor  = el.textContent.trim();  /* texte exact du lien */

      let params = "";
      if (valId)   params += "&val_id="     + encodeURIComponent(valId);
      if (valFile) params += "&val_file="   + encodeURIComponent(valFile);
      if (valStatus) params += "&val_status=" + encodeURIComponent(valStatus);
      if (ctx)     params += "&ctx="        + encodeURIComponent(ctx.substring(0, 400));
      if (anchor)  params += "&anchor="     + encodeURIComponent(anchor.substring(0, 200));

      window.open(href + "?" + params.replace(/^&/, ""), "_blank");
    }});
  }});

  var currentLink = null;

  document.addEventListener("mouseover", function(e) {{
    const el = e.target.closest("a.source-ref");
    if (!el) return;
    currentLink = el;
    const label = el.getAttribute("title") || "";
    if (!label) return;
    tip.textContent = label;
    tip.style.opacity = "1";
  }});

  document.addEventListener("mousemove", function(e) {{
    if (tip.style.opacity !== "1") return;
    let x = e.clientX + 14;
    let y = e.clientY + 18;
    if (x + 460 > window.innerWidth) x = e.clientX - 460;
    if (y + 80  > window.innerHeight) y = e.clientY - 50;
    tip.style.left = x + "px";
    tip.style.top  = y + "px";
  }});

  document.addEventListener("mouseout", function(e) {{
    /* Masquer seulement si on quitte vraiment le lien (pas vers un enfant) */
    const el = e.target.closest("a.source-ref");
    if (!el) return;
    const to = e.relatedTarget;
    if (to && el.contains(to)) return;
    tip.style.opacity = "0";
    currentLink = null;
  }});
}})();

/* ------------------------------------------------------------------ */
/* 6. Légende des statuts de validation                                */
/* ------------------------------------------------------------------ */
(function() {{
  const legend = document.createElement("div");
  legend.id = "status-legend";
  const items = [
    ["#d42b2b", "Structure initiale"],
    ["#e07820", "Notes développées"],
    ["#c8a800", "Rédigé"],
    ["#2e78c8", "Révisé"],
    ["#111111", "Validé"],
  ];
  let inner = '<div class="legend-title">Statut des sections</div>';
  items.forEach(function(item) {{
    inner += '<div>'
      + '<span class="l-dot" style="background:' + item[0] + '"></span>'
      + item[1]
      + '</div>';
  }});
  legend.innerHTML = inner;
  document.body.appendChild(legend);
}})();
/* ------------------------------------------------------------------ */
/* 7. Validation interactive des éléments inline (.val, .val-cite…)  */
/* ------------------------------------------------------------------ */
(function() {{
  const STATUS_ORDER  = [
    'brouillon', 'à revoir', 'revu', 'validé'
  ];
  const STATUS_COLORS = {{
    'brouillon': '#d42b2b', 'à revoir': '#e07820',
    'revu': '#2e78c8', 'validé': '#111111'
  }};
  const STATUS_DOT_CLASSES = {{
    'brouillon': 'status-brouillon', 'à revoir': 'status-arevoir',
    'revu': 'status-revu', 'validé': 'status-valide'
  }};

  function rankOf(status) {{
    const idx = STATUS_ORDER.indexOf(status);
    return idx === -1 ? 0 : idx;
  }}

  /* — Cascade : recalcule les dots des titres à partir des éléments [data-val-id] — */
  function updateCascade() {{
    const content = document.getElementById('content');
    if (!content) return;

    function minRankIn(container) {{
      const vals = container.querySelectorAll('[data-val-id]');
      if (!vals.length) return -1;
      let min = STATUS_ORDER.length - 1;
      vals.forEach(function(v) {{
        const s = v.getAttribute('data-val-status') || 'brouillon';
        const r = rankOf(s);
        if (r < min) min = r;
      }});
      return min;
    }}

    function updateDot(heading, rank) {{
      const dot = heading.querySelector('.status-dot');
      if (!dot) return;
      const newStatus = STATUS_ORDER[rank] || 'brouillon';
      Object.values(STATUS_DOT_CLASSES).forEach(function(cls) {{
        dot.classList.remove(cls);
      }});
      dot.classList.add(STATUS_DOT_CLASSES[newStatus] || 'status-brouillon');
      dot.setAttribute('title', newStatus);
    }}

    /* Pour chaque niveau de titre, chercher la section repliable suivante */
    [1, 2, 3, 4].forEach(function(level) {{
      content.querySelectorAll('h' + level).forEach(function(h) {{
        /* La section repliable créée par le JS collapse vient après le titre */
        let sec = h.nextElementSibling;
        while (sec && !sec.classList.contains('collapsible-section')) {{
          sec = sec.nextElementSibling;
        }}
        if (!sec) return;
        const rank = minRankIn(sec);
        if (rank >= 0) updateDot(h, rank);
      }});
    }});
  }}

  /* — Popup — */
  const popup = document.createElement('div');
  popup.id = 'val-popup';
  document.body.appendChild(popup);

  let currentEl      = null;
  let selectedStatus = null;
  let originalStatus = null;

  function openPopup(el, clientX, clientY) {{
    currentEl      = el;
    originalStatus = el.getAttribute('data-val-status') || 'brouillon';
    selectedStatus = originalStatus;
    const text = (el.textContent || '').trim().substring(0, 45);

    /* — Barre de segments toggle — */
    let segs = '';
    STATUS_ORDER.forEach(function(s) {{
      const col        = STATUS_COLORS[s] || '#999';
      const isCurrent  = s === originalStatus ? ' current' : '';
      const isActive   = s === originalStatus ? ' active'  : '';
      segs += '<button class="vp-seg' + isCurrent + isActive + '" data-status="' + s + '">'
        + '<span class="vp-seg-dot" style="background:' + col + '"></span>'
        + '<span class="vp-seg-label">' + s + '</span>'
        + '</button>';
    }});

    popup.innerHTML =
      '<div class="vp-title">Modifier le statut</div>'
      + '<div class="vp-label" title="' + text + '">' + (text || '(élément)') + '…</div>'
      + '<div class="vp-toggle-bar">' + segs + '</div>'
      + '<div class="vp-actions">'
      + '<button class="vp-btn cancel">Annuler</button>'
      + '<button class="vp-btn confirm" disabled>Enregistrer</button>'
      + '</div>';

    /* Positionnement */
    popup.classList.add('open');
    const pw = popup.offsetWidth  || 340;
    const ph = popup.offsetHeight || 160;
    let px = clientX + 12, py = clientY + 12;
    if (px + pw > window.innerWidth  - 8) px = clientX - pw - 12;
    if (py + ph > window.innerHeight - 8) py = clientY - ph - 12;
    popup.style.left = Math.max(8, px) + 'px';
    popup.style.top  = Math.max(8, py) + 'px';

    /* Clics sur les segments */
    const confirmBtn = popup.querySelector('.confirm');
    popup.querySelectorAll('.vp-seg').forEach(function(seg) {{
      seg.addEventListener('click', function() {{
        popup.querySelectorAll('.vp-seg').forEach(function(s) {{ s.classList.remove('active'); }});
        seg.classList.add('active');
        selectedStatus = seg.getAttribute('data-status');
        /* Activer Enregistrer uniquement si l'état a changé */
        confirmBtn.disabled = (selectedStatus === originalStatus);
      }});
    }});

    popup.querySelector('.cancel').addEventListener('click', closePopup);
    popup.querySelector('.confirm').addEventListener('click', function() {{
      if (!this.disabled) {{
        submitValidation(currentEl, selectedStatus);
      }}
    }});
  }}

  function closePopup() {{
    popup.classList.remove('open');
    currentEl = null;
  }}

  function submitValidation(el, newStatus) {{
    const file = el.getAttribute('data-val-file') || '';
    const id   = el.getAttribute('data-val-id')   || '';
    if (!file || !id) {{
      alert('Attributs data-val-file ou data-val-id manquants sur cet élément.');
      closePopup();
      return;
    }}
    fetch('/validate', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{file: file, id: id, status: newStatus}})
    }}).then(function(r) {{
      if (r.ok) {{
        el.setAttribute('data-val-status', newStatus);
        closePopup();
        updateCascade();
      }} else {{
        r.text().then(function(t) {{ alert('Erreur serveur : ' + t); }});
        closePopup();
      }}
    }}).catch(function() {{
      alert('Impossible de contacter le serveur de prévisualisation.');
      closePopup();
    }});
  }}

  /* Attacher les gestionnaires de clic droit à tous les éléments annotés */
  document.querySelectorAll('[data-val-id]').forEach(function(el) {{
    el.addEventListener('contextmenu', function(e) {{
      e.preventDefault();
      e.stopPropagation();
      openPopup(el, e.clientX, e.clientY);
    }});
  }});

  /* Fermer le popup si clic gauche en dehors */
  document.addEventListener('click', function(e) {{
    if (popup.classList.contains('open') && !popup.contains(e.target)) {{
      closePopup();
    }}
  }});

  /* Lancer la cascade initiale après que les sections repliables soient créées */
  setTimeout(updateCascade, 100);
}})();
</script>

{TEXT_EDIT_SCRIPT}
</body>
</html>"""
    return html


def update_val_element_status(content: str, elem_id: str, new_status: str):
    """Met à jour data-val-status="..." pour l'élément avec data-val-id=elem_id.

    Retourne le contenu modifié, ou None si l'élément est introuvable.
    """
    # Trouver la balise ouvrante qui contient data-val-id="<elem_id>"
    tag_pattern = re.compile(
        r'<[a-zA-Z]+\b[^>]*\bdata-val-id="' + re.escape(elem_id) + r'"[^>]*>',
        re.DOTALL,
    )
    m = tag_pattern.search(content)
    if not m:
        return None

    old_tag = m.group(0)
    # Vérifier que l'attribut est présent avant de tenter le remplacement
    if 'data-val-status=' not in old_tag:
        return None  # Attribut absent dans la balise

    # Remplacer data-val-status dans la balise trouvée
    # Note : pas de \b car le nom d'attribut contient des tirets (non-word chars)
    new_tag = re.sub(
        r'data-val-status="[^"]*"',
        f'data-val-status="{new_status}"',
        old_tag,
    )
    # Retourner le contenu (même si la valeur est identique — no-op idempotent)
    return content[: m.start()] + new_tag + content[m.end() :]


# ---------------------------------------------------------------------------
# Gestion du démarrage : libération du port et contrôle du navigateur

def kill_port(port: int) -> bool:
    """Termine tout processus qui écoute sur le port donné.

    Retourne True si au moins un processus a été tué (= relance),
    False si le port était libre (= premier démarrage).
    """
    killed = False
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding="cp1252",
            errors="replace",
        )
        my_pid = str(os.getpid())
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and pid != my_pid:
                    subprocess.run(
                        ["taskkill", "/PID", pid, "/F"],
                        capture_output=True,
                    )
                    print(f"[INIT] Ancien processus {pid} sur le port {port} terminé.")
                    killed = True
    except Exception as exc:
        print(f"[INIT] Avertissement : impossible de vérifier le port {port} : {exc}")
    if killed:
        time.sleep(1)  # Laisser le port se libérer
    return killed


def rebuild(source: str = "", *, text_edit=False):
    """Reconstruit la page : assembleur + HTML + notification navigateurs."""
    global _html_cache
    if source:
        print(f"[WATCHER] Modification détectée : {source}")
    with _rebuild_lock, tempfile.TemporaryDirectory() as temp_dir:
        preview_path = pathlib.Path(temp_dir) / "preview.md"
        ok = run_assembler(preview_path)
        if not ok and text_edit:
            raise ValueError("Échec de l’assemblage du bulletin.")
        if not text_edit:
            run_regime_dashboard()
        html = build_html(preview_path if ok else None)
        with _html_lock:
            _html_cache = html
    notify_clients()
    print("[PREVIEW] Page mise à jour")


# ---------------------------------------------------------------------------
# Watchdog — surveillance des fichiers

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self._timer = None
        self._lock  = threading.Lock()

    def on_modified(self, event):
        path = pathlib.Path(event.src_path)
        # Ignorer dossiers, fichiers de sortie et types non pertinents
        if event.is_directory:
            return
        if "10_output" in str(path):
            return
        if path.suffix not in (".md", ".yml", ".yaml", ".css", ".py"):
            return
        # Debounce : déclencher seulement si pas de modif depuis 1 s
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(1.0, rebuild, args=[path.name])
            self._timer.start()


# ---------------------------------------------------------------------------
# Serveur HTTP

class PreviewHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Silencer les logs HTTP

    def handle_error(self, request, client_address):
        pass  # Silencer les erreurs de connexion Windows (WinError 10053 etc.)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            pass

    def do_GET(self):
        if self.path == "/":
            self._serve_html()
        elif self.path == "/events":
            self._serve_sse()
        elif self.path == "/dashboard":
            self._serve_dashboard()
        elif self.path == "/api/text-edit/files":
            self._serve_text_edit_files()
        elif urlparse(self.path).path == "/api/text-edit":
            self._serve_text_edit_file()
        elif self.path in ("/export", "/export-notes"):
            self._handle_export(include_notes=(self.path == "/export-notes"))
        elif self.path in ("/export-word", "/export-word/start"):
            self._start_export_word()
        elif self.path == "/export-word/status":
            self._serve_export_word_status()
        elif self.path == "/export-word/download":
            self._download_export_word()
        elif self.path == "/download":
            self._handle_download()
        elif self.path == "/api/dashboard-settings":
            self._serve_dashboard_settings()
        elif self.path == "/api/questionnaire-data":
            self._serve_questionnaire_data()
        elif self.path == "/api/prestation-settings":
            self._serve_prestation_settings()
        elif self.path.startswith("/api/denom/"):
            self._serve_denom_api()
        elif self.path.startswith("/files/"):
            self._serve_file()
        elif self.path.startswith("/output/"):
            self._serve_output_static()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_dashboard_settings(self):
        payload = {"oddDecisions": {}, "denomSettings": {}}
        if DASHBOARD_SETTINGS_FILE.exists():
            try:
                raw = DASHBOARD_SETTINGS_FILE.read_text(encoding="utf-8")
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    odd = parsed.get("oddDecisions")
                    payload["oddDecisions"] = odd if isinstance(odd, dict) else {}
                    denom = parsed.get("denomSettings")
                    payload["denomSettings"] = denom if isinstance(denom, dict) else {}
            except (OSError, json.JSONDecodeError):
                payload = {"oddDecisions": {}, "denomSettings": {}}

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_questionnaire_data(self):
        """GET /api/questionnaire-data — retourne questionnaire_data.json."""
        if QUESTIONNAIRE_DATA_FILE.exists():
            try:
                raw = QUESTIONNAIRE_DATA_FILE.read_text(encoding="utf-8")
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError("questionnaire_data.json doit contenir un objet")
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                body = json.dumps(
                    {"error": f"Lecture de questionnaire_data.json impossible : {exc}"},
                    ensure_ascii=False,
                ).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
        else:
            data = {}
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _handle_questionnaire_data(self):
        """POST|PUT /api/questionnaire-data — sauvegarde questionnaire_data.json."""
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("JSON doit être un objet")
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Corps JSON invalide")
            return
        try:
            QUESTIONNAIRE_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            QUESTIONNAIRE_DATA_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Erreur d'ecriture questionnaire_data.json")
            return
        resp = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(resp)

    def _serve_prestation_settings(self):
        """GET /api/prestation-settings — retourne prestation_settings.json."""
        if PRESTATION_SETTINGS_FILE.exists():
            try:
                raw = PRESTATION_SETTINGS_FILE.read_text(encoding="utf-8")
                data = json.loads(raw)
            except (OSError, json.JSONDecodeError):
                data = {}
        else:
            data = {}
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _handle_prestation_settings(self):
        """POST|PUT /api/prestation-settings — sauvegarde prestation_settings.json."""
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("JSON doit être un objet")
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Corps JSON invalide")
            return
        try:
            PRESTATION_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            PRESTATION_SETTINGS_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Erreur d'ecriture prestation_settings.json")
            return
        resp = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(resp)

    def _serve_denom_api(self):
        parsed = urlparse(self.path)
        route = parsed.path
        qs = parse_qs(parsed.query)

        if route == "/api/denom/local":
            self._serve_denom_local(qs)
            return

        if route == "/api/denom/wpp":
            year = qs.get("year", [""])[0]
            if not re.fullmatch(r"\d{4}", year):
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(b'{"error":"Parametre year invalide"}')
                return
            target_url = f"https://www.populationpyramid.net/api/pp/180/{year}/"
            attempts = 1
        elif route == "/api/denom/wb":
            indicator = qs.get("indicator", [""])[0]
            allowed_indicators = {
                "SP.POP.TOTL",
                "SP.POP.0014.TO",
                "SP.POP.1564.TO",
                "SP.POP.65UP.TO",
                "SP.DYN.CBRT.IN",
            }
            if indicator not in allowed_indicators:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(b'{"error":"Indicateur Banque mondiale invalide"}')
                return
            target_url = (
                "https://api.worldbank.org/v2/country/CD/indicator/"
                f"{indicator}?format=json&per_page=200"
            )
            attempts = 3
        elif route == "/api/denom/ilo":
            target_url = (
                "https://rplumber.ilo.org/data/indicator/"
                "?id=EMP_TEMP_SEX_AGE_NB_A&ref_area=COD&sex=SEX_T"
                "&classif1=AGE_AGGREGATE_TOTAL&time_from=2000&time_to=2030"
                "&type=label&decimals=0"
            )
            attempts = 1
        else:
            self.send_response(404)
            self.end_headers()
            return

        req = Request(
            target_url,
            headers={
                "User-Agent": "RDC-Bulletin-Preview/1.0",
                "Accept": "application/json,text/plain,*/*",
            },
            method="GET",
        )
        try:
            for attempt in range(attempts):
                try:
                    with urlopen(req, timeout=15) as resp:
                        body = resp.read()
                        status = getattr(resp, "status", 200)
                        content_type = resp.headers.get("Content-Type", "application/json")
                    break
                except (HTTPError, URLError, TimeoutError):
                    if attempt + 1 >= attempts:
                        raise
                    time.sleep(0.4 * (attempt + 1))
        except HTTPError as err:
            status = err.code if err.code else 502
            body = err.read() if hasattr(err, "read") else b""
            if not body:
                body = json.dumps({"error": f"Upstream HTTP {status}"}).encode("utf-8")
            content_type = err.headers.get("Content-Type", "application/json") if err.headers else "application/json"
        except URLError as err:
            status = 502
            body = json.dumps({"error": f"Upstream indisponible: {err.reason}"}).encode("utf-8")
            content_type = "application/json"
        except TimeoutError:
            status = 504
            body = json.dumps({"error": "Delai d'attente de la source depasse"}).encode("utf-8")
            content_type = "application/json"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_denom_local(self, qs):
        """GET /api/denom/local — interroge denominateurs_ref dans la base SQLite locale.

        Paramètres (query string) :
          var_code   : code variable (ex. var-c-popsx)   — requis
          sex        : classe sexe   (ex. sex-t)          — requis
          age        : classe âge    (ex. age-0+)         — requis
          iso3       : code pays     (défaut : COD)
          year_start : année début   (défaut : 2015)
          year_end   : année fin     (défaut : 2027)

        Réponse JSON : [{year, value, source, source_note}]
        """
        def _err(code, msg):
            body = json.dumps({"error": msg}, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        var_code = (qs.get("var_code", [""])[0] or "").strip()
        sex      = (qs.get("sex",      [""])[0] or "").strip()
        age      = (qs.get("age",      [""])[0] or "").strip()
        iso3     = (qs.get("iso3",     ["COD"])[0] or "COD").strip()

        try:
            year_start = int(qs.get("year_start", ["2015"])[0])
            year_end   = int(qs.get("year_end",   ["2027"])[0])
        except (ValueError, TypeError):
            return _err(400, "Paramètres year_start / year_end invalides")

        if not var_code or not sex or not age:
            return _err(400, "Paramètres var_code, sex et age requis")

        if not DENOMINATEURS_DB_FILE.exists():
            return _err(503, "Base de données locale introuvable. Lancer : py 09_scripts/import_denominateurs_excel.py")

        try:
            con = sqlite3.connect(str(DENOMINATEURS_DB_FILE), timeout=10)
            cur = con.cursor()
            cur.execute(
                """SELECT year, val_n, source, source_note
                   FROM denominateurs_ref
                   WHERE iso3 = ? AND var_code = ? AND class_sex = ? AND class_age = ?
                     AND year >= ? AND year <= ?
                     AND val_n IS NOT NULL
                   ORDER BY year""",
                (iso3, var_code, sex, age, year_start, year_end),
            )
            rows = cur.fetchall()
            con.close()
        except sqlite3.Error as err:
            return _err(500, f"Erreur base de données : {err}")

        result = [
            {"year": r[0], "value": r[1], "source": r[2], "source_note": r[3]}
            for r in rows
        ]
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/validate":
            self._handle_validate()
        elif self.path == "/api/text-edit/save":
            self._handle_text_edit_save()
        elif self.path == "/api/dashboard-settings":
            self._handle_dashboard_settings()
        elif self.path == "/api/questionnaire-data":
            self._handle_questionnaire_data()
        elif self.path == "/api/prestation-settings":
            self._handle_prestation_settings()
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if self.path == "/api/questionnaire-data":
            self._handle_questionnaire_data()
        elif self.path == "/api/prestation-settings":
            self._handle_prestation_settings()
        else:
            self.send_response(405)
            self.end_headers()

    def _send_text_edit_json(self, status_code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_text_edit_files(self):
        try:
            sources = _text_edit_sources()
        except (OSError, UnicodeError, ValueError) as exc:
            self._send_text_edit_json(500, {"error": f"Lecture des sections impossible : {exc}"})
            return
        files = [
            {"file": source["file"], "title": source["title"]}
            for source in sources.values()
        ]
        self._send_text_edit_json(200, {"files": files})

    def _serve_text_edit_file(self):
        query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        file_values = query.get("file", [])
        if len(file_values) != 1 or not file_values[0]:
            self._send_text_edit_json(400, {"error": "Le paramètre file est requis."})
            return
        try:
            source = _text_edit_sources(file_values[0]).get(file_values[0])
        except (OSError, UnicodeError, ValueError) as exc:
            self._send_text_edit_json(500, {"error": f"Lecture de la section impossible : {exc}"})
            return
        if source is None:
            self._send_text_edit_json(404, {"error": "Cette rubrique ne contient pas de texte public modifiable. Choisissez une autre rubrique du sommaire."})
            return
        self._send_text_edit_json(200, {
            "file": source["file"],
            "title": source["title"],
            "html": _visual_text_document(source)["html"],
            "revision": source["revision"],
        })

    def _same_origin_local_request(self) -> bool:
        origin = urlparse(self.headers.get("Origin", ""))
        request_host = urlparse("//" + self.headers.get("Host", ""))
        return (
            origin.scheme == "http"
            and origin.hostname in {"localhost", "127.0.0.1", "::1"}
            and origin.hostname == request_host.hostname
            and origin.port == PORT
        )

    def _handle_text_edit_save(self):
        if not self._same_origin_local_request():
            self._send_text_edit_json(403, {"error": "La sauvegarde doit provenir de la prévisualisation locale."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_text_edit_json(400, {"error": "Longueur de requête invalide."})
            return
        if length <= 0 or length > TEXT_EDIT_MAX_BODY_BYTES:
            self._send_text_edit_json(413, {"error": "Le contenu est vide ou dépasse la taille autorisée."})
            return

        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_text_edit_json(400, {"error": "Corps JSON invalide."})
            return
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("file"), str)
            or not isinstance(data.get("revision"), str)
            or not isinstance(data.get("changes"), dict)
        ):
            self._send_text_edit_json(400, {"error": "Champs requis : file, revision et changes."})
            return

        file_rel = data["file"]

        with _text_edit_lock:
            try:
                source = _text_edit_sources(file_rel).get(file_rel)
            except (OSError, UnicodeError, ValueError) as exc:
                self._send_text_edit_json(500, {"error": f"Lecture de la source impossible : {exc}"})
                return
            if source is None:
                self._send_text_edit_json(403, {"error": "Cette source n'est pas autorisée à l'édition."})
                return
            if data["revision"] != source["revision"]:
                self._send_text_edit_json(409, {
                    "error": "Le fichier source a changé depuis son ouverture. Rechargez la section avant de sauvegarder."
                })
                return

            try:
                latest_bytes = source["target"].read_bytes()
            except OSError as exc:
                self._send_text_edit_json(500, {"error": f"Relecture de la source impossible : {exc}"})
                return
            if hashlib.sha256(latest_bytes).hexdigest() != source["revision"]:
                self._send_text_edit_json(409, {
                    "error": "Le fichier source a changé pendant la sauvegarde. Rechargez la section."
                })
                return

            try:
                edited_body = _apply_visual_text_changes(source, data["changes"])
                updated_bytes = _build_text_edit_update(source, edited_body)
            except ValueError as exc:
                self._send_text_edit_json(400, {"error": str(exc)})
                return
            try:
                source["target"].write_bytes(updated_bytes)
            except OSError as exc:
                self._send_text_edit_json(500, {"error": f"Écriture du fichier source impossible : {exc}"})
                return

        try:
            rebuild(file_rel, text_edit=True)
        except (OSError, ValueError) as exc:
            self._send_text_edit_json(500, {"error": f"Texte enregistré, mais prévisualisation non actualisée : {exc}"})
            return
        self._send_text_edit_json(200, {"ok": True})
        print(f"[TEXT_EDIT] {file_rel}")

    def _handle_dashboard_settings(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            try:
                body_str = body.decode("utf-8")
            except UnicodeDecodeError:
                body_str = body.decode("latin-1")
            data = json.loads(body_str)
            if not isinstance(data, dict):
                raise ValueError("corps JSON invalide")
            odd_decisions = data.get("oddDecisions")
            if odd_decisions is not None and not isinstance(odd_decisions, dict):
                raise ValueError("oddDecisions doit être un objet")
            denom_settings = data.get("denomSettings")
            if denom_settings is not None and not isinstance(denom_settings, dict):
                raise ValueError("denomSettings doit être un objet")
        except (json.JSONDecodeError, ValueError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Corps JSON invalide. Champs admis : oddDecisions (objet), denomSettings (objet)")
            return

        DASHBOARD_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing = {"oddDecisions": {}, "denomSettings": {}}
        if DASHBOARD_SETTINGS_FILE.exists():
            try:
                parsed = json.loads(DASHBOARD_SETTINGS_FILE.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    existing_odd = parsed.get("oddDecisions")
                    existing_denom = parsed.get("denomSettings")
                    existing["oddDecisions"] = existing_odd if isinstance(existing_odd, dict) else {}
                    existing["denomSettings"] = existing_denom if isinstance(existing_denom, dict) else {}
            except (OSError, json.JSONDecodeError):
                existing = {"oddDecisions": {}, "denomSettings": {}}

        payload = {
            "oddDecisions": odd_decisions if odd_decisions is not None else existing["oddDecisions"],
            "denomSettings": denom_settings if denom_settings is not None else existing["denomSettings"],
        }
        try:
            DASHBOARD_SETTINGS_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Impossible d'ecrire dashboard_settings.json")
            return

        response_body = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response_body)

    def _handle_validate(self):
        """Endpoint POST /validate — met à jour data-val-status dans le fichier source."""
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            # Décoder avec UTF-8, puis Latin-1 en repli (navigateurs Windows)
            try:
                body_str = body.decode("utf-8")
            except UnicodeDecodeError:
                body_str = body.decode("latin-1")
            data       = json.loads(body_str)
            file_rel   = data["file"]
            elem_id    = data["id"]
            new_status = data["status"]
        except (json.JSONDecodeError, KeyError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Corps JSON invalide. Champs requis : file, id, status")
            return

        # Contrôle de sécurité — interdire les traversées de répertoire
        try:
            target = (WORKSPACE_DIR / file_rel).resolve()
            if not str(target).startswith(str(WORKSPACE_DIR.resolve())):
                self.send_response(403)
                self.end_headers()
                return
            if not target.exists() or not target.is_file():
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Fichier source introuvable")
                return
        except Exception as exc:
            self.send_response(400)
            self.end_headers()
            return

        content     = target.read_text(encoding="utf-8")
        new_content = update_val_element_status(content, elem_id, new_status)
        if new_content is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"Élément data-val-id=\"{elem_id}\" introuvable dans {file_rel}".encode("utf-8")
            )
            return

        target.write_text(new_content, encoding="utf-8")
        response_body = json.dumps({"ok": True}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response_body)
        print(f"[VALIDATE] {elem_id} → {new_status} ({file_rel})")

    def _handle_export(self, include_notes: bool = False):
        """GET /export ou /export-notes — Génère le HTML autonome et redirige vers lui."""
        from datetime import datetime as _dt
        exporter = SCRIPT_DIR / "exporter.py"
        stamp = _dt.now().strftime("%Y-%m-%d")
        label = "notes" if include_notes else "relecture"
        export_file = WORKSPACE_DIR / "10_output" / f"bulletin_{label}_{stamp}.html"

        if not exporter.exists():
            self.send_response(503)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"exporter.py introuvable dans 09_scripts/")
            return

        cmd = [sys.executable, str(exporter)]
        if include_notes:
            cmd.append("--notes")
        else:
            cmd.append("--html")

        result = subprocess.run(
            cmd,
            capture_output=True,
            cwd=str(WORKSPACE_DIR),
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0 or not export_file.exists():
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            err = (result.stderr or result.stdout or "Erreur inconnue")[:800]
            self.wfile.write(
                f"Erreur lors de la génération du fichier HTML :\n\n{err}".encode("utf-8")
            )
            return

        redirect_url = f"/files/10_output/bulletin_{label}_{stamp}.html"
        self.send_response(302)
        self.send_header("Location", redirect_url)
        self.end_headers()
        print(f"[EXPORT] Fichier généré : bulletin_{label}_{stamp}.html")

    def _word_export_paths(self):
        from datetime import datetime as _dt
        stamp = _dt.now().strftime("%Y-%m-%d")
        export_file = WORKSPACE_DIR / "10_output" / f"bulletin_relecture_{stamp}.docx"
        filename = f"bulletin_relecture_{stamp}.docx"
        return export_file, filename

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _start_export_word(self):
        """Démarre l'export Word en arrière-plan et répond immédiatement."""
        exporter = SCRIPT_DIR / "exporter.py"
        if not exporter.exists():
            self._send_json({"status": "error", "error": "exporter.py introuvable dans 09_scripts/"}, 503)
            return

        with _word_export_lock:
            if _word_export_state["status"] == "running":
                self._send_json({"status": "running"})
                return
            _word_export_state.update(status="running", error="", filename="")

        threading.Thread(target=self._run_export_word, daemon=True).start()
        self._send_json({"status": "running"}, 202)

    @staticmethod
    def _run_export_word():
        """Exécute le pipeline Word hors du thread de la requête HTTP."""
        from datetime import datetime as _dt
        exporter = SCRIPT_DIR / "exporter.py"
        stamp = _dt.now().strftime("%Y-%m-%d")
        export_file = WORKSPACE_DIR / "10_output" / f"bulletin_relecture_{stamp}.docx"
        filename = export_file.name

        try:
            result = subprocess.run(
                [sys.executable, str(exporter), "--word"],
                capture_output=True,
                cwd=str(WORKSPACE_DIR),
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0 or not export_file.exists():
                err = (result.stderr or result.stdout or "Erreur inconnue")[-2000:]
                raise RuntimeError(err.strip())
        except (OSError, RuntimeError) as exc:
            with _word_export_lock:
                _word_export_state.update(status="error", error=str(exc), filename="")
            print(f"[EXPORT WORD] Échec : {exc}")
            return

        with _word_export_lock:
            _word_export_state.update(status="done", error="", filename=filename)
        print(f"[EXPORT WORD] Fichier prêt : {filename}")

    def _serve_export_word_status(self):
        with _word_export_lock:
            payload = dict(_word_export_state)
        self._send_json(payload)

    def _download_export_word(self):
        export_file, filename = self._word_export_paths()
        with _word_export_lock:
            state = dict(_word_export_state)
        if state["status"] != "done" or not export_file.exists():
            self._send_json(
                {"status": state["status"], "error": state["error"] or "Aucun export Word prêt."},
                409,
            )
            return

        try:
            data = export_file.read_bytes()
        except OSError as exc:
            self._send_json({"status": "error", "error": str(exc)}, 500)
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
        print(f"[EXPORT WORD] Fichier servi : {filename}")

    def _handle_export_word(self):
        """Compatibilité interne : démarre désormais l'export asynchrone."""
        self._start_export_word()

    def _handle_download(self):
        """GET /download — Génère le HTML autonome et le sert en téléchargement direct."""
        from datetime import datetime as _dt
        exporter = SCRIPT_DIR / "exporter.py"
        stamp = _dt.now().strftime("%Y-%m-%d")
        export_file = WORKSPACE_DIR / "10_output" / f"bulletin_relecture_{stamp}.html"
        filename = f"bulletin_relecture_{stamp}.html"

        if not exporter.exists():
            self.send_response(503)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"exporter.py introuvable dans 09_scripts/")
            return

        result = subprocess.run(
            [sys.executable, str(exporter), "--html"],
            capture_output=True,
            cwd=str(WORKSPACE_DIR),
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0 or not export_file.exists():
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            err = (result.stderr or result.stdout or "Erreur inconnue")[:800]
            self.wfile.write(
                f"Erreur lors de la génération du fichier HTML :\n\n{err}".encode("utf-8")
            )
            return

        data = export_file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
        print(f"[DOWNLOAD] Fichier téléchargé : {filename}")

    def _serve_dashboard(self):
        """Sert le tableau de bord interactif depuis 10_output/dashboard_regimes.html."""
        dashboard = REGIME_DASHBOARD
        if REGIME_VISUALIZER.exists():
            try:
                if _dashboard_refresh_required(dashboard):
                    run_regime_dashboard()
            except OSError:
                pass
        if not dashboard.exists():
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h2>Tableau de bord introuvable</h2>"
                b"<p>Lancer d'abord : <code>py 09_scripts/visualiser_regimes.py</code></p>"
            )
            return
        html = dashboard.read_text(encoding="utf-8")
        # Réécrire uniquement les fichiers statiques connus de 10_output/
        # (remplacement ciblé pour éviter de toucher le JS inline ou les liens d'onglets)
        _static_files = [
            "questionnaire_modal.js",
            "questionnaire_modal.css",
            "branch_fusion.js",
            "unit_conversion.js",
            "prestation_settings.js",
            "dashboard_main.js",
        ]
        for _fname in _static_files:
            # Cache-busting : suffixe ?v=<mtime> pour forcer le navigateur à
            # re-télécharger le fichier dès qu'il change sur le disque. Évite
            # qu'un onglet ouvert avant une régénération exécute un JS périmé.
            _fpath = WORKSPACE_DIR / "10_output" / _fname
            try:
                _ver = int(_fpath.stat().st_mtime)
            except OSError:
                _ver = 0
            _versioned = f"/output/{_fname}?v={_ver}"
            html = html.replace(f'src="{_fname}"', f'src="{_versioned}"')
            html = html.replace(f"src='{_fname}'", f"src='{_versioned}'")
            html = html.replace(f'href="{_fname}"', f'href="{_versioned}"')
            html = html.replace(f"href='{_fname}'", f"href='{_versioned}'")
        content = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _serve_output_static(self):
        """Sert les fichiers statiques de 10_output/ via /output/<fichier>."""
        import mimetypes
        from urllib.parse import unquote, urlparse
        rel = unquote(urlparse(self.path).path[len("/output/"):])
        # Empêche les path traversal
        if ".." in rel or rel.startswith("/"):
            self.send_response(403)
            self.end_headers()
            return
        target = WORKSPACE_DIR / "10_output" / rel
        if not target.exists() or not target.is_file():
            self.send_response(404)
            self.end_headers()
            return
        mime, _ = mimetypes.guess_type(str(target))
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _serve_file(self):
        """Sert un fichier du workspace via /files/<chemin_relatif>.

        Pour les fichiers .txt de sources (dans 06_sources/), génère une
        page HTML avec le contenu du fichier + liens vers la source web
        et vers le fichier local.
        """
        import mimetypes
        from urllib.parse import urlparse, parse_qs, unquote
        parsed   = urlparse(self.path)
        rel      = unquote(parsed.path[7:])  # retirer "/files/" et décoder %20, accents…
        qs       = parse_qs(parsed.query)
        val_id     = qs.get("val_id",     [""])[0]
        val_file   = qs.get("val_file",   [""])[0]
        val_status = qs.get("val_status", ["brouillon"])[0]
        ctx        = qs.get("ctx",        [""])[0]
        anchor     = qs.get("anchor",     [""])[0]
        try:
            target = (WORKSPACE_DIR / rel).resolve()
            if not str(target).startswith(str(WORKSPACE_DIR.resolve())):
                self.send_response(403)
                self.end_headers()
                return
            if not target.exists() or not target.is_file():
                self.send_response(404)
                self.end_headers()
                return

            # Fichiers .txt de sources → page HTML enrichie
            if target.suffix.lower() == ".txt" and (
                "06_sources" in str(target) or
                "08_figures/donnees" in str(target).replace("\\", "/")
            ):
                data = self._build_source_viewer(
                    target, rel, val_id, val_file, val_status, ctx, anchor
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return

            mime, _ = mimetypes.guess_type(str(target))
            mime = mime or "application/octet-stream"
            # Forcer charset=utf-8 pour tous les fichiers texte
            if mime == "text/plain":
                mime = "text/plain; charset=utf-8"
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            if "text/plain" in mime or mime == "application/pdf":
                self.send_header("Content-Disposition", "inline")
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            print(f"[FICHIER] Erreur : {exc}")
            self.send_response(500)
            self.end_headers()

    @staticmethod
    def _build_source_viewer(path: pathlib.Path, rel: str,
                              val_id: str = "", val_file: str = "",
                              val_status: str = "brouillon",
                              ctx: str = "", anchor: str = "") -> str:
        """Génère une page HTML pour afficher un fichier source .txt."""
        content = path.read_text(encoding="utf-8-sig")

        # Extraire les métadonnées de l'en-tête (tolérant aux variantes de clés)
        meta = {}
        for line in content.splitlines():
            m = re.match(r"^\s*([A-Za-zÀ-ÖØ-öø-ÿ0-9_ \-]+?)\s*:\s*(.+?)\s*$", line)
            if not m:
                continue
            key = m.group(1).strip()
            val = m.group(2).strip()
            if val:
                meta.setdefault(key, []).append(val)

        def _extend_http_urls(container, values):
            for v in values:
                if not isinstance(v, str):
                    continue
                for u in re.findall(r"https?://[^\s<>\"]+", v):
                    if u not in container:
                        container.append(u)

        # Plusieurs URLs possibles (URL, URL_API, URL_VERIFICATION, LIEN SOURCE, etc.)
        urls = []
        canonical_url_keys = (
            "URL",
            "URL_2",
            "URL_3",
            "URL_API",
            "URL_VERIFICATION",
            "URL_SOURCE",
            "URL_PDF_DIRECT",
            "URL_COUNTRY_BRIEF",
        )
        for key in canonical_url_keys:
            _extend_http_urls(urls, meta.get(key, []))

        for key, vals in meta.items():
            key_up = key.upper()
            if key_up.startswith("LIEN SOURCE"):
                _extend_http_urls(urls, vals)

        # Fallback ultime : première(s) URL(s) trouvée(s) dans le contenu brut
        if not urls:
            _extend_http_urls(urls, [content])

        source = meta.get("SOURCE", ["—"])[0]
        titre  = meta.get("TITRE",  ["—"])[0]
        niveau = meta.get("NIVEAU", ["—"])[0]
        consult = (
            meta.get("CONSULTÉ", ["—"])[0]
            if "CONSULTÉ" in meta else
            meta.get("CONSULTE", ["—"])[0]
        )

        # Construire les badges de lien
        web_links = ""
        for url in urls:
            url = url.strip()
            if url.startswith("http"):
                web_links += (
                    f'<a href="{url}" target="_blank" rel="noopener" class="btn-link web">'
                    f'🌐 Ouvrir la source en ligne</a>\n'
                )

        # Chercher un PDF local du même nom que le .txt
        pdf_path = path.with_suffix(".pdf")
        pdf_rel  = rel.rsplit(".", 1)[0] + ".pdf"
        if pdf_path.exists():
            local_link = (
                f'<a href="/files/{pdf_rel}" target="_blank" class="btn-link local">'
                f'📄 Ouvrir le PDF local</a>'
            )
        elif urls:
            # Pas de PDF local → renvoyer vers l'URL web comme fallback
            first_url = next((u.strip() for u in urls if u.strip().startswith("http")), "")
            if first_url:
                local_link = (
                    f'<a href="{first_url}" target="_blank" rel="noopener" class="btn-link local">'
                    f'🔗 Accéder à la source (aucun PDF local)</a>'
                )
            else:
                local_link = ""
        else:
            local_link = (
                f'<span class="btn-link local" style="opacity:0.4;cursor:default">'
                f'📂 Aucun fichier local disponible</span>'
            )

        # Échapper le contenu texte pour HTML
        import html as html_lib
        content_escaped = html_lib.escape(content)

        # Bloc contexte (phrase source avec ancre surlignée)
        ctx_block = ""
        if ctx:
            # Surligner l'ancre dans le texte du contexte
            if anchor:
                import re as _re
                ctx_html = html_lib.escape(ctx)
                anchor_esc = html_lib.escape(anchor)
                # Remplacer la première occurrence (insensible à la casse)
                ctx_html = _re.sub(
                    '(' + _re.escape(anchor_esc) + ')',
                    r'<mark class="ctx-anchor">\1</mark>',
                    ctx_html, count=1, flags=_re.IGNORECASE
                )
            else:
                ctx_html = html_lib.escape(ctx)
            ctx_block = f"""
<div id="ctx-section">
  <div class="ctx-label">📝 Contexte d'utilisation dans le bulletin</div>
  <blockquote id="ctx-text">{ctx_html}</blockquote>
</div>"""

        # Bloc de validation (affiché seulement si val_id et val_file sont présents)
        STATUS_COLORS_PY = {
            "brouillon": "#d42b2b",
            "à revoir":  "#e07820",
            "revu":      "#2e78c8",
            "validé":    "#1a6e3c",
        }
        STATUS_ORDER_PY = ["brouillon", "à revoir", "revu", "validé"]

        val_block = ""
        if val_id and val_file:
            cur_col = STATUS_COLORS_PY.get(val_status, "#999")
            segs_html = ""
            for s in STATUS_ORDER_PY:
                col = STATUS_COLORS_PY.get(s, "#999")
                is_current = " current" if s == val_status else ""
                is_active  = " active"  if s == val_status else ""
                segs_html += (
                    f'<button class="vseg{is_current}{is_active}" data-status="{html_lib.escape(s)}">'
                    f'<span class="vseg-dot" style="background:{col}"></span>'
                    f'<span class="vseg-label">{html_lib.escape(s)}</span>'
                    f'</button>'
                )
            val_block = f"""
<div id="val-section">
  <div class="val-title">Statut de validation :
    <span id="val-current-badge" style="display:inline-block;padding:2px 10px;border-radius:10px;
                 background:{cur_col};color:#fff;font-size:11px;font-weight:700;
                 margin-left:6px;letter-spacing:0.5px">{html_lib.escape(val_status)}</span>
  </div>
  <div class="val-subtitle">Modifier le statut :</div>
  <div id="val-toggle-bar">{segs_html}</div>
  <div id="val-actions">
    <button id="val-save" onclick="saveValidation()" disabled>💾 Enregistrer</button>
    <span id="val-msg"></span>
  </div>
</div>
<script>
  var originalStatus = {json.dumps(val_status)};
  var selectedStatus = originalStatus;
  var saveBtn = document.getElementById('val-save');
  document.querySelectorAll('.vseg').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      document.querySelectorAll('.vseg').forEach(function(b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      selectedStatus = btn.getAttribute('data-status');
      saveBtn.disabled = (selectedStatus === originalStatus);
    }});
  }});
  function saveValidation() {{
    if (saveBtn.disabled) return;
    var msg = document.getElementById('val-msg');
    msg.textContent = '…';
    fetch('/validate', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        file: {json.dumps(val_file)},
        id:   {json.dumps(val_id)},
        status: selectedStatus
      }})
    }})
    .then(function(r) {{ return r.text().then(function(t) {{ return {{ok: r.ok, text: t}}; }}); }})
    .then(function(res) {{
      if (res.ok) {{
        msg.style.color = '#1a6e3c';
        msg.textContent = '✓ Enregistré — ' + selectedStatus;
        originalStatus = selectedStatus;
        saveBtn.disabled = true;
        /* Mettre à jour le badge statut courant */
        var badge = document.getElementById('val-current-badge');
        if (badge) {{
          badge.textContent = selectedStatus;
        }}
        /* Marquer le segment comme état de référence */
        document.querySelectorAll('.vseg').forEach(function(b) {{ b.classList.remove('current'); }});
        document.querySelectorAll('.vseg').forEach(function(b) {{
          if (b.getAttribute('data-status') === selectedStatus) b.classList.add('current');
        }});
      }} else {{
        msg.style.color = '#d42b2b';
        msg.textContent = '✗ Erreur : ' + res.text;
      }}
    }})
    .catch(function(e) {{ msg.style.color='#d42b2b'; msg.textContent='✗ ' + e; }});
  }}
</script>"""

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_lib.escape(titre[:60])} — Source</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f2f1ec;
            color: #1c1c1c; min-height: 100vh; }}
    #header {{
      background: #1a3a6b; color: #fff; padding: 18px 32px;
      border-bottom: 3px solid #c8a951;
    }}
    #header .badge {{
      display: inline-block; background: #c8a951; color: #1a1a1a;
      font-size: 10px; font-weight: 700; padding: 2px 9px;
      border-radius: 10px; text-transform: uppercase; letter-spacing: 1px;
      margin-bottom: 8px;
    }}
    #header h1 {{ font-size: 17px; font-weight: 700; line-height: 1.4;
                  margin-bottom: 4px; }}
    #header .meta {{ font-size: 12px; color: #b8c4d4; margin-top: 6px; }}
    #header .meta span {{ margin-right: 18px; }}
    #links {{
      display: flex; gap: 12px; flex-wrap: wrap;
      padding: 14px 32px; background: #fff;
      border-bottom: 1px solid #d0cfc8;
    }}
    .btn-link {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 7px 16px; border-radius: 5px; font-size: 13px;
      font-weight: 600; text-decoration: none; transition: background 0.12s;
      border: 1px solid transparent;
    }}
    .btn-link.web {{ background: #1a3a6b; color: #fff; border-color: #1a3a6b; }}
    .btn-link.web:hover {{ background: #254a8e; }}
    .btn-link.local {{ background: #fff; color: #1a3a6b; border-color: #1a3a6b; }}
    .btn-link.local:hover {{ background: #eef2f9; }}
    /* Bloc contexte */
    #ctx-section {{
      max-width: 900px; margin: 20px auto 0;
      background: #fffdf5; border: 1px solid #e8d98a; border-radius: 6px;
      padding: 14px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .ctx-label {{
      font-size: 11px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 1px; color: #a08020; margin-bottom: 8px;
    }}
    #ctx-text {{
      font-size: 14px; line-height: 1.7; color: #333;
      border-left: 3px solid #c8a951; padding-left: 14px;
      font-style: italic;
    }}
    mark.ctx-anchor {{
      background: #fff0a0;
      color: #7a4f00;
      font-weight: 700;
      font-style: normal;
      border-radius: 3px;
      padding: 0 3px;
      box-shadow: 0 0 0 1px #c8a951;
    }}
    /* Bloc validation */
    #val-section {{
      max-width: 900px; margin: 20px auto 0;
      background: #fff; border: 1px solid #d0cfc8; border-radius: 6px;
      padding: 16px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .val-title {{
      font-size: 13px; font-weight: 700; color: #333;
      margin-bottom: 14px; display: flex; align-items: center; gap: 8px;
    }}
    .val-subtitle {{
      font-size: 11px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 1px; color: #aaa; margin-bottom: 8px;
    }}
    /* — Toggle bar — */
    #val-toggle-bar {{
      display: flex; flex-direction: row;
      border: 1px solid #dde; border-radius: 6px;
      overflow: hidden; margin-bottom: 14px;
    }}
    .vseg {{
      flex: 1; display: flex; flex-direction: column;
      align-items: center; gap: 5px;
      padding: 9px 6px 8px;
      cursor: pointer; border: none; border-right: 1px solid #dde;
      background: #f8f8fb; font-size: 11px;
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #99a; transition: background 0.12s, color 0.12s;
      position: relative; outline: none;
    }}
    .vseg:last-child {{ border-right: none; }}
    .vseg-dot {{
      width: 10px; height: 10px; border-radius: 50%;
      display: block; opacity: 0.28;
      transition: opacity 0.12s, transform 0.12s;
    }}
    .vseg.current::after {{
      content: ''; position: absolute; bottom: 3px; left: 50%;
      transform: translateX(-50%); width: 20px; height: 2px;
      border-radius: 1px; background: #b0b8c8;
    }}
    .vseg.active {{
      background: #fff; color: #223; font-weight: 700;
      box-shadow: inset 0 0 0 1px rgba(0,0,0,0.08);
    }}
    .vseg.active .vseg-dot {{ opacity: 1; transform: scale(1.2); }}
    .vseg:not(.active):hover {{ background: #eef0f8; color: #445; }}
    .vseg:not(.active):hover .vseg-dot {{ opacity: 0.65; }}
    #val-actions {{ display: flex; align-items: center; gap: 14px; }}
    #val-save {{
      padding: 7px 20px; background: #1a3a6b; color: #fff; border: none;
      border-radius: 5px; font-size: 13px; font-weight: 600; cursor: pointer;
      transition: background 0.12s;
    }}
    #val-save:hover:not(:disabled) {{ background: #254a8e; }}
    #val-save:disabled {{
      background: #c8cdd8; color: #e8eaf0; cursor: not-allowed; opacity: 0.75;
    }}
    #val-msg {{ font-size: 12px; font-style: italic; }}
    /* Contenu */
    #content {{
      max-width: 900px; margin: 20px auto; background: #fff;
      border: 1px solid #d0cfc8; border-radius: 6px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.07); overflow: hidden;
    }}
    #content-header {{
      background: #f4f3ee; border-bottom: 1px solid #d0cfc8;
      padding: 10px 20px; font-size: 11px; color: #888;
      font-family: monospace; letter-spacing: 0.3px;
    }}
    pre {{
      padding: 20px 24px; font-family: 'Courier New', monospace;
      font-size: 13px; line-height: 1.75; white-space: pre-wrap;
      word-break: break-word; color: #1c1c1c;
    }}
    .back-link {{
      display: block; text-align: center; padding: 18px;
      font-size: 12px; color: #667; text-decoration: none;
    }}
    .back-link:hover {{ color: #1a3a6b; }}
  </style>
</head>
<body>
<div id="header">
  <div class="badge">📄 Fiche source — Bulletin RDC 2026</div>
  <h1>{html_lib.escape(titre)}</h1>
  <div class="meta">
    <span>📚 {html_lib.escape(source)}</span>
    <span>🔍 Niveau {html_lib.escape(niveau)}</span>
    <span>📅 Consulté le {html_lib.escape(consult)}</span>
  </div>
</div>

<div id="links">
  {web_links}
  {local_link}
</div>

{ctx_block}

{val_block}

<div id="content">
  <div id="content-header">📁 {html_lib.escape(rel)}</div>
  <pre>{content_escaped}</pre>
</div>

<a class="back-link" href="javascript:window.close()">✕ Fermer cet onglet</a>
</body>
</html>"""

    def _serve_html(self):
        with _html_lock:
            data = _html_cache.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _serve_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        q = queue.Queue(maxsize=10)
        with _clients_lock:
            _clients.append(q)

        try:
            while True:
                try:
                    msg = q.get(timeout=25)
                    self.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # Heartbeat pour maintenir la connexion
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)


# ---------------------------------------------------------------------------
# Point d'entrée

if __name__ == "__main__":
    # Lire les arguments CLI
    no_browser = "--no-browser" in sys.argv

    print("=" * 60)
    print("  Serveur de prévisualisation — Bulletin RDC 2026")
    print("=" * 60)

    # Libérer le port (tuer les anciens processus)
    print(f"\n[INIT] Vérification du port {PORT}…")
    was_running = kill_port(PORT)
    if was_running:
        print(f"[INIT] Port {PORT} libéré. Redémarrage en cours…")
    else:
        print(f"[INIT] Port {PORT} libre.")

    # Premier build
    print("[INIT] Construction initiale de la page…")
    rebuild()

    # Watchdog
    observer = Observer()
    observer.schedule(ChangeHandler(), str(WORKSPACE_DIR), recursive=True)
    observer.start()
    print("[WATCHER] Surveillance des fichiers activée")

    # Serveur HTTP
    class RobustHTTPServer(http.server.ThreadingHTTPServer):
        """Serveur robuste aux erreurs de connexion Windows (WinError 10053 etc.)"""
        def handle_error(self, request, client_address):
            import sys
            exc = sys.exc_info()[1]
            if isinstance(exc, (ConnectionAbortedError, ConnectionResetError,
                                BrokenPipeError, OSError)):
                return  # Ignorer silencieusement les erreurs de connexion
            super().handle_error(request, client_address)

    server = RobustHTTPServer(("localhost", PORT), PreviewHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://localhost:{PORT}"
    print(f"\n[OK] Serveur demarre -> {url}")
    print("[OK] Ctrl+C pour arrêter\n")

    # Ouvrir le navigateur uniquement si :
    # - ce n'est pas une relance (port était libre)
    # - ET l'option --no-browser n'est pas passée
    if not was_running and not no_browser:
        print("[OK] Ouverture du navigateur…")
        threading.Timer(1.0, webbrowser.open, args=[url]).start()
    elif was_running:
        print("[OK] Relance détectée — la page existante se rafraîchit automatiquement.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[ARRÊT] Fermeture du serveur…")
        server.shutdown()
        observer.stop()
        observer.join()
        print("[ARRÊT] OK")
    except Exception as exc:
        print(f"\n[ERREUR] Exception inattendue dans la boucle principale : {exc}")
        import traceback; traceback.print_exc()
