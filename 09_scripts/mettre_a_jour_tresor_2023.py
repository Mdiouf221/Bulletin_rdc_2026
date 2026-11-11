"""Met à jour l'hypothèse TRESOR 2023 avec la référence ILOSTAT 2020.

Le classeur ESS est conservé tel quel, à l'exception des deux cellules qui portent
l'estimation résiduelle : l'inventaire du régime et sa prestation associée.
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parent.parent
WORKBOOK = WORKSPACE / "06_sources" / "ESS" / "ESS_TRESOR" / "EST TRESOR 2023.xlsm"
OLD_FORMULA = "<f>1425000 - 1004106</f><v>420894</v>"
NEW_FORMULA = "<f>1622972 - 1004106</f><v>618866</v>"
TARGET_SHEETS = ("xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml")


def main() -> int:
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Classeur introuvable : {WORKBOOK}")

    with zipfile.ZipFile(WORKBOOK) as source:
        contents = {entry.filename: source.read(entry.filename) for entry in source.infolist()}

    for sheet_name in TARGET_SHEETS:
        content = contents.get(sheet_name)
        if content is None:
            raise RuntimeError(f"Feuille XML introuvable : {sheet_name}")
        old_count = content.count(OLD_FORMULA.encode("utf-8"))
        if old_count != 1:
            raise RuntimeError(
                f"Formule attendue absente ou ambiguë dans {sheet_name} ({old_count} occurrence(s))."
            )
        contents[sheet_name] = content.replace(
            OLD_FORMULA.encode("utf-8"),
            NEW_FORMULA.encode("utf-8"),
            1,
        )

    with tempfile.NamedTemporaryFile(
        dir=WORKBOOK.parent,
        prefix=f"{WORKBOOK.stem}_",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
            for name, content in contents.items():
                target.writestr(name, content)
        os.replace(temp_path, WORKBOOK)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    print("OK: TRESOR 2023 = 1 622 972 - 1 004 106 = 618 866.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
