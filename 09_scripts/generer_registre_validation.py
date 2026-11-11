"""Génère le registre séparé des valeurs annotées par data-val-id."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "10_output" / "registre_verification_donnees.md"
SCAN_DIRS = (
    "01_pages_preliminaires",
    "02_introduction_generale",
    "03_chapitres",
    "04_annexes",
)

ANNOTATION_RE = re.compile(
    r"<(?P<tag>span|a)\b(?P<attrs>[^>]*\bdata-val-id=[\"'](?P<id>[^\"']+)[\"'][^>]*)>"
    r"(?P<text>.*?)</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
STATUS_RE = re.compile(r'\bdata-val-status=["\']([^"\']+)["\']', re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip().replace("|", r"\|")


def collect_rows() -> list[tuple[str, str, str, str, int]]:
    rows = []
    for directory in SCAN_DIRS:
        for path in sorted((ROOT / directory).rglob("*.md")):
            text = path.read_text(encoding="utf-8-sig")
            for match in ANNOTATION_RE.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                status_match = STATUS_RE.search(match.group("attrs"))
                status = status_match.group(1) if status_match else "à valider"
                rows.append(
                    (
                        match.group("id"),
                        status,
                        clean_text(match.group("text")),
                        path.relative_to(ROOT).as_posix(),
                        line,
                    )
                )
    return rows


def main() -> None:
    rows = collect_rows()
    duplicate_ids = len(rows) - len({row[0] for row in rows})
    lines = [
        "# Registre de vérification des données",
        "",
        "> Document de suivi séparé du bulletin imprimable. Les éléments marqués "
        "`à valider`, `à rédiger` ou `structure initiale` apparaissent en rouge "
        "dans l’export imprimable.",
        "",
        f"Éléments annotés : **{len(rows)}**  ",
        f"Identifiants dupliqués détectés : **{duplicate_ids}**",
        "",
        "| Identifiant | Statut | Valeur ou passage | Fichier source | Ligne | Action attendue |",
        "|---|---|---|---|---:|---|",
    ]
    for identifier, status, value, path, line in rows:
        action = "Vérifier la source et confirmer la valeur." if status in {
            "à valider",
            "à rédiger",
            "structure initiale",
        } else "Aucune action en attente."
        lines.append(
            f"| `{identifier}` | {status} | {value or '[contenu non textuel]'} "
            f"| `{path}` | {line} | {action} |"
        )
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} annotations enregistrées dans {OUTPUT}")


if __name__ == "__main__":
    main()
