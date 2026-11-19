import json
import html
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import serveur_preview


class DashboardRefreshRequiredTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _touch(self, path: Path, mtime: float) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
        path.touch()
        import os
        os.utime(path, (mtime, mtime))
        return path

    def test_returns_true_when_dashboard_missing(self):
        dashboard = self.tmp_dir / "dashboard.html"
        dep = self._touch(self.tmp_dir / "visualiser.py", 100)
        with patch.object(serveur_preview, "REGIME_VISUALIZER", dep), patch.object(
            serveur_preview, "REGIME_DB_FILE", dep
        ), patch.object(serveur_preview, "DENOMINATEURS_DB_FILE", dep):
            self.assertTrue(serveur_preview._dashboard_refresh_required(dashboard))

    def test_returns_true_when_regime_db_is_newer(self):
        dashboard = self._touch(self.tmp_dir / "dashboard.html", 100)
        visualizer = self._touch(self.tmp_dir / "visualiser.py", 90)
        regime_db = self._touch(self.tmp_dir / "regime.db", 110)
        denom_db = self._touch(self.tmp_dir / "denom.db", 80)
        with patch.object(serveur_preview, "REGIME_VISUALIZER", visualizer), patch.object(
            serveur_preview, "REGIME_DB_FILE", regime_db
        ), patch.object(serveur_preview, "DENOMINATEURS_DB_FILE", denom_db):
            self.assertTrue(serveur_preview._dashboard_refresh_required(dashboard))

    def test_returns_false_when_dependencies_are_not_newer(self):
        dashboard = self._touch(self.tmp_dir / "dashboard.html", 100)
        visualizer = self._touch(self.tmp_dir / "visualiser.py", 100)
        regime_db = self._touch(self.tmp_dir / "regime.db", 99)
        denom_db = self._touch(self.tmp_dir / "denom.db", 98)
        with patch.object(serveur_preview, "REGIME_VISUALIZER", visualizer), patch.object(
            serveur_preview, "REGIME_DB_FILE", regime_db
        ), patch.object(serveur_preview, "DENOMINATEURS_DB_FILE", denom_db):
            self.assertFalse(serveur_preview._dashboard_refresh_required(dashboard))


class TextEditorHelperTests(unittest.TestCase):
    def test_partial_manual_edit_keeps_text_on_both_sides_after_save(self):
        begin, end = serveur_preview.MANUAL_EDIT_START, serveur_preview.MANUAL_EDIT_END
        body = f"Avant.\r\n\r\n{begin}\r\nPassage modifié.\r\n{end}\r\n\r\nAprès."
        source = {"body": body, "tables": [], "prefix": "", "suffix": "",
                  "raw_bytes": body.encode("utf-8")}
        slots = serveur_preview._visual_text_document(source)["slots"]
        self.assertEqual([slot["text"] for slot in slots.values()],
                         ["Avant.", "Passage modifié.", "Après."])
        edited = serveur_preview._apply_visual_text_changes(source, {"2": "Suite."})
        saved = serveur_preview._build_text_edit_update(source, edited).decode("utf-8")
        self.assertEqual((saved.count(begin), saved.count(end)), (1, 1))
        reopened = serveur_preview._visual_text_document({"body": saved})
        self.assertEqual([slot["text"] for slot in reopened["slots"].values()],
                         ["Avant.", "Passage modifié.", "Suite."])
        for invalid in (body.replace(end, ""), end + body + begin, end + "Texte" + begin):
            with self.assertRaises(ValueError):
                serveur_preview._unwrap_manual_edit(invalid)

    def test_partial_bold_roundtrip_preserves_annotation_and_literal_text(self):
        body = '<a class="source-ref" href="/files/test.pdf">Une donnée</a>'
        updated = serveur_preview._apply_visual_text_changes({"body": body}, {"0": [
            {"text": "Une ", "bold": False}, {"text": "<donnée>", "bold": True},
        ]})
        self.assertIn("<strong>&lt;donnée&gt;</strong>", updated)
        slots = serveur_preview._visual_text_document({"body": updated})["slots"]
        slot = next(key for key, value in slots.items() if value["bold"])
        restored = serveur_preview._apply_visual_text_changes({"body": updated}, {
            slot: [{"text": "donnée", "bold": False}],
        })
        self.assertEqual(restored, body)

    def test_remove_bold_from_part_of_existing_markdown(self):
        source = {"body": "Du **texte important** ici."}
        updated = serveur_preview._apply_visual_text_changes(source, {"1": [
            {"text": "texte ", "bold": False}, {"text": "important", "bold": True},
        ]})
        self.assertEqual(updated, "Du texte <strong>important</strong> ici.")

    def test_visual_editor_preserves_markup_sources_and_tables(self):
        body = (
            '\n### Un titre <span class="valid-badge nv">non validé</span>\n\n'
            'Un **texte important** et '
            '<a href="/files/source.pdf" class="source-ref" data-val-id="s1-d1"'
            ' data-val-status="à valider">une donnée</a>.\n\n'
            '| A | B |\n| --- | --- |\n| 12 | 34 |\n'
        )
        masked, tables = serveur_preview._mask_readonly_tables(body)
        source = {
            "body": body, "content": masked, "tables": tables,
            "prefix": "## Texte rédigé\n", "suffix": "",
            "raw_bytes": body.encode("utf-8"),
        }
        document = serveur_preview._visual_text_document(source)
        slot = next(
            key for key, value in document["slots"].items()
            if value["text"] == "une donnée"
        )
        self.assertNotIn("12", [value["text"] for value in document["slots"].values()])
        self.assertNotIn("non validé", [value["text"] for value in document["slots"].values()])
        self.assertIn("<strong>", document["html"])
        self.assertIn("<table>", document["html"])

        updated = serveur_preview._apply_visual_text_changes(source, {slot: "une correction"})
        updated = serveur_preview._restore_readonly_tables(updated, tables)
        self.assertIn('data-val-id="s1-d1"', updated)
        self.assertIn('data-val-status="à valider">une correction</a>', updated)
        self.assertIn("**texte important**", updated)
        self.assertIn("| 12 | 34 |", updated)

    def test_visual_editor_keeps_generated_blocks_readonly_and_edits_following_text(self):
        generated = (
            "<!-- AUTO_GENERE:indicateur:DEBUT -->\n"
            "Texte calculé automatiquement.\n\n"
            "| A |\n| --- |\n| 12 |\n"
            "<!-- AUTO_GENERE:indicateur:FIN -->"
        )
        body = "Texte rédigé manuellement.\n\n" + generated + "\n\nTexte final."
        document = serveur_preview._visual_text_document({"body": body})
        self.assertIn("Texte calculé automatiquement.", document["html"])
        self.assertNotIn(
            "Texte calculé automatiquement.", [value["text"] for value in document["slots"].values()]
        )
        slot = next(
            key for key, value in document["slots"].items() if value["text"] == "Texte final."
        )
        changed = serveur_preview._apply_visual_text_changes({"body": body}, {slot: "Texte corrigé."})
        _, tables = serveur_preview._mask_readonly_tables(body)
        restored = serveur_preview._restore_readonly_tables(changed, tables)
        self.assertIn(generated, restored)
        self.assertIn("Texte corrigé.", html.unescape(restored))

    def test_visual_input_cannot_inject_html_or_markdown_and_can_be_reopened(self):
        body = "\nTexte initial.\n"
        source = {"body": body}
        document = serveur_preview._visual_text_document(source)
        slot = next(iter(document["slots"]))
        literal = '<script>alert(1)</script> **gras** & suite'
        updated = serveur_preview._apply_visual_text_changes(source, {slot: literal})
        self.assertNotIn("<script>", updated)
        self.assertNotIn("**gras**", updated)
        reopened = serveur_preview._visual_text_document({"body": updated})
        self.assertIn(literal, [value["text"] for value in reopened["slots"].values()])

    def test_visual_editor_normalizes_wrapped_paragraphs_without_changing_source(self):
        for newline in ("\n", "\r\n", "\r"):
            with self.subTest(newline=repr(newline)):
                body = newline + "Un paragraphe" + newline + "sur deux lignes." + newline
                source = {"body": body}
                document = serveur_preview._visual_text_document(source)
                self.assertEqual(len(document["slots"]), 1)
                slot = next(iter(document["slots"]))
                self.assertEqual(document["slots"][slot]["text"], "Un paragraphe sur deux lignes.")
                changed = serveur_preview._apply_visual_text_changes(
                    source, {slot: "Un paragraphe corrigé."}
                )
                self.assertEqual(
                    html.unescape(changed),
                    newline + "Un paragraphe corrigé." + newline,
                )

    def test_visual_editor_can_delete_windows_multiline_text_before_source_link(self):
        body = (
            "\r\nPremier passage.\r\nDeuxième passage.\r\nTroisième passage.\r\n\r\n"
            '<a href="/files/source.pdf" data-val-id="s1-d1">Une référence</a>.\r\n'
        )
        document = serveur_preview._visual_text_document({"body": body})
        slot = next(
            key for key, value in document["slots"].items()
            if value["text"].startswith("Premier passage.")
        )
        changed = serveur_preview._apply_visual_text_changes({"body": body}, {slot: ""})
        self.assertEqual(
            changed,
            '\r\n\r\n\r\n<a href="/files/source.pdf" data-val-id="s1-d1">Une référence</a>.\r\n',
        )
        reference_slot = next(
            key for key, value in document["slots"].items()
            if value["text"] == "Une référence"
        )
        changed = serveur_preview._apply_visual_text_changes(
            {"body": body}, {reference_slot: "Référence corrigée"}
        )
        self.assertEqual(changed, body.replace("Une référence", "Référence corrigée"))

    def test_text_section_split_includes_all_public_subsections(self):
        source = (
            "# Section\n"
            "<!-- NOTE_INTERNE\nStatut : rédigé\n-->\n"
            "## Texte rédigé\n\nTexte à modifier.\n\n"
            "## Autre partie\nContenu intact.\n"
        )

        prefix, body, suffix = serveur_preview._split_text_edit_section(source)

        self.assertIn("NOTE_INTERNE", prefix)
        self.assertEqual(body, "\nTexte à modifier.\n\n## Autre partie\nContenu intact.\n")
        self.assertEqual(suffix, "")

    def test_sources_include_unmarked_sections_nested_chapters_and_table_only_files(self):
        documents = {
            "cartographie.md": (
                "## 3.1 Cartographie\n\n"
                "<!-- NOTE_INTERNE\n## Texte rédigé\nNote confidentielle.\n-->\n\n"
                "### Vue d'ensemble\nTexte de la cartographie.\n"
            ),
            "chapitre.md": (
                "# Chapitre 5\n<!-- NOTE_INTERNE\nPlan interne.\n-->\n"
                "## Texte rédigé\n\n"
                "## 5.1 Premier indicateur\nTexte du premier indicateur.\n\n"
                "## 5.2 Second indicateur\nTexte du second indicateur.\n"
            ),
            "annexe.md": (
                "# Annexe A\n<!-- NOTE_INTERNE\nPlan de l'annexe.\n-->\n\n"
                "## A.1 Champ\nPremier texte.\n\n## A.2 Classification\nDernier texte.\n"
            ),
            "sigles.md": (
                "# Sigles\n## Texte rédigé\n\n"
                "| Sigle | Sens |\n| --- | --- |\n| OIT | Organisation |\n"
            ),
            "entete.md": "# Chapitre 6\n<!-- NOTE_INTERNE\nPlan seulement.\n-->\n",
            "hors_assemblage.md": "# Ancienne section\n## Texte rédigé\nTexte exclu.\n",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "03_chapitres"
            source_dir.mkdir()
            for name, text in documents.items():
                (source_dir / name).write_text(text, encoding="utf-8")
            configured = [name for name in documents if name != "hors_assemblage.md"]
            (root / "build_config.yml").write_text(
                "sections:\n  - files:\n"
                + "".join(f'      - "03_chapitres/{name}"\n' for name in configured),
                encoding="utf-8",
            )
            with patch.object(serveur_preview, "WORKSPACE_DIR", root):
                sources = serveur_preview._text_edit_sources()

            self.assertEqual(
                set(sources),
                {f"03_chapitres/{name}" for name in configured if name != "entete.md"},
            )
            cartographie = sources["03_chapitres/cartographie.md"]
            self.assertIn("Note confidentielle.", cartographie["prefix"])
            self.assertNotIn(
                "Note confidentielle.", serveur_preview._visual_text_document(cartographie)["html"]
            )
            chapter = serveur_preview._visual_text_document(sources["03_chapitres/chapitre.md"])
            self.assertIn("Texte du premier indicateur.", chapter["html"])
            self.assertIn("Texte du second indicateur.", chapter["html"])
            annexe = serveur_preview._visual_text_document(sources["03_chapitres/annexe.md"])
            self.assertIn("Dernier texte.", annexe["html"])
            sigles = serveur_preview._visual_text_document(sources["03_chapitres/sigles.md"])
            self.assertIn("<table>", sigles["html"])
            self.assertEqual(sigles["slots"], {})

    def test_saving_late_subsection_preserves_internal_notes_tables_and_prior_text(self):
        for marker in ("", "## Texte rédigé\r\n"):
            with self.subTest(marker=bool(marker)):
                prefix = (
                    "# Annexe\r\n<!-- NOTE_INTERNE\r\nPlan initial.\r\n-->\r\n"
                    + marker
                )
                table = "| A |\r\n| --- |\r\n| Valeur protégée |\r\n"
                internal_note = "<!-- NOTE_INTERNE\r\nNote à préserver.\r\n-->"
                body = (
                    "\r\n## A.1 Première partie\r\nPremier texte.\r\n\r\n"
                    + table + "\r\n" + internal_note
                    + "\r\n\r\n## A.2 Seconde partie\r\nDernier texte.\r\n"
                )
                source_text = prefix + body
                before, editable, suffix = serveur_preview._split_text_edit_section(source_text)
                _, tables = serveur_preview._mask_readonly_tables(editable)
                source = {
                    "prefix": before, "body": editable, "suffix": suffix,
                    "tables": tables, "raw_bytes": source_text.encode("utf-8"),
                }
                document = serveur_preview._visual_text_document(source)
                self.assertNotIn("Note à préserver.", document["html"])
                slot = next(
                    key for key, value in document["slots"].items()
                    if value["text"] == "Dernier texte."
                )
                changed = serveur_preview._apply_visual_text_changes(source, {slot: "Texte corrigé."})
                updated = serveur_preview._build_text_edit_update(source, changed).decode("utf-8")
                self.assertTrue(updated.startswith(prefix))
                self.assertIn(table, updated)
                self.assertIn(internal_note, updated)
                self.assertIn("Premier texte.", updated)
                self.assertIn("Texte corrigé.", html.unescape(updated))
                self.assertNotIn("Dernier texte.", updated)
                _, reopened_body, _ = serveur_preview._split_text_edit_section(updated)
                reopened = serveur_preview._visual_text_document({"body": reopened_body})
                self.assertIn(
                    "Texte corrigé.", [value["text"] for value in reopened["slots"].values()]
                )

    def test_tables_are_masked_and_restored_without_editing_them(self):
        source = (
            "Texte avant.\n\n"
            "| Colonne A | Colonne B |\n"
            "| --- | --- |\n"
            "| Valeur 1 | Valeur 2 |\n\n"
            "Texte après."
        )

        masked, tables = serveur_preview._mask_readonly_tables(source)

        self.assertEqual(len(tables), 1)
        self.assertNotIn("Valeur 1", masked)
        edited = masked.replace("Texte avant.", "Texte modifié.")
        restored = serveur_preview._restore_readonly_tables(edited, tables)
        self.assertIn("| Valeur 1 | Valeur 2 |", restored)
        self.assertIn("Texte modifié.", restored)
        self.assertEqual(restored, source.replace("Texte avant.", "Texte modifié."))

    def test_table_repere_must_remain_unchanged(self):
        masked, tables = serveur_preview._mask_readonly_tables(
            "Avant.\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n"
        )
        altered = serveur_preview.TABLE_TOKEN_RE.sub("", masked)

        with self.assertRaises(ValueError):
            serveur_preview._restore_readonly_tables(altered, tables)

    def test_manual_edit_markers_render_a_highlight_wrapper(self):
        source = (
            serveur_preview.MANUAL_EDIT_START
            + "\nTexte édité.\n"
            + serveur_preview.MANUAL_EDIT_END
        )

        rendered = serveur_preview._render_manual_edit_markers(source)

        self.assertIn('<div class="manual-edit" markdown="1">', rendered)
        self.assertIn("</div>", rendered)

    def test_build_update_preserves_notes_tables_and_following_content(self):
        source_text = (
            "# Section\n"
            "<!-- NOTE_INTERNE\nStatut : rédigé\n-->\n"
            "## Texte rédigé\n\n"
            "Texte initial.\n\n"
            "| Colonne |\n"
            "| --- |\n"
            "| Valeur protégée |\n\n"
            "## Section suivante\nContenu intact.\n"
        )
        prefix, body, suffix = serveur_preview._split_text_edit_section(source_text)
        masked, tables = serveur_preview._mask_readonly_tables(body)
        source = {
            "prefix": prefix,
            "body": body,
            "suffix": suffix,
            "tables": tables,
            "raw_bytes": b"\xef\xbb\xbf" + source_text.encode("utf-8"),
        }

        updated_bytes = serveur_preview._build_text_edit_update(
            source, masked.replace("Texte initial.", "Texte modifié.")
        )
        updated = updated_bytes.decode("utf-8-sig")
        updated_prefix, updated_body, updated_suffix = (
            serveur_preview._split_text_edit_section(updated)
        )

        self.assertTrue(updated_bytes.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(updated_prefix, prefix)
        self.assertEqual(updated_suffix, suffix)
        self.assertIn("NOTE_INTERNE", updated)
        self.assertIn("| Valeur protégée |", updated_body)
        self.assertIn("## Section suivante\nContenu intact.", updated_body)
        self.assertIn(serveur_preview.MANUAL_EDIT_START, updated_body)
        self.assertIn("Texte modifié.", html.unescape(updated_body))

    def test_save_endpoint_updates_only_text_in_an_allowed_source_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "03_chapitres" / "test_section.md"
            source_path.parent.mkdir(parents=True)
            original = (
                "# Section\n"
                "<!-- NOTE_INTERNE\nStatut : rédigé\n-->\n"
                "## Texte rédigé\n\nTexte initial.\n\n"
                "| Colonne |\n| --- |\n| Valeur protégée |\n\n"
                "## Section suivante\nContenu intact.\n"
            )
            source_path.write_text(original, encoding="utf-8")
            (root / "build_config.yml").write_text(
                'project:\n  title: Test bulletin\noutputs:\n'
                '  working_markdown: 10_output/travail.md\n'
                '  publication_markdown: 10_output/publication.md\n'
                'sections:\n  - files:\n      - "03_chapitres/test_section.md"\n',
                encoding="utf-8",
            )

            assembler = root / "09_scripts" / "assembler_markdown.py"
            assembler.parent.mkdir()
            shutil.copyfile(serveur_preview.ASSEMBLER, assembler)
            with patch.object(serveur_preview, "WORKSPACE_DIR", root), \
                    patch.object(serveur_preview, "ASSEMBLER", assembler), \
                    patch.object(serveur_preview, "_html_cache", ""):
                httpd = ThreadingHTTPServer(
                    ("127.0.0.1", 0), serveur_preview.PreviewHandler
                )
                port = httpd.server_address[1]
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                try:
                    base_url = f"http://127.0.0.1:{port}"
                    with patch.object(serveur_preview, "PORT", port):
                        with urlopen(base_url + "/api/text-edit/files") as response:
                            files = json.loads(response.read().decode("utf-8"))["files"]
                        self.assertEqual(len(files), 1)

                        with urlopen(
                            base_url + "/api/text-edit?file=03_chapitres%2Ftest_section.md"
                        ) as response:
                            section = json.loads(response.read().decode("utf-8"))
                        self.assertIn("Valeur protégée", section["html"])
                        self.assertIn('data-text-slot="0"', section["html"])

                        payload = json.dumps({
                            "file": section["file"],
                            "revision": section["revision"],
                            "changes": {"0": "Texte modifié."},
                        }).encode("utf-8")
                        tampered_payload = json.dumps({
                            "file": section["file"],
                            "revision": section["revision"],
                            "changes": {"table-0": "Valeur altérée"},
                        }).encode("utf-8")
                        tampered_request = Request(
                            base_url + "/api/text-edit/save",
                            data=tampered_payload,
                            headers={
                                "Content-Type": "application/json",
                                "Origin": base_url,
                            },
                            method="POST",
                        )
                        with self.assertRaises(HTTPError) as invalid_table:
                            urlopen(tampered_request)
                        self.assertEqual(invalid_table.exception.code, 400)
                        self.assertEqual(source_path.read_text(encoding="utf-8"), original)

                        cross_origin_request = Request(
                            base_url + "/api/text-edit/save",
                            data=payload,
                            headers={
                                "Content-Type": "application/json",
                                "Origin": "http://example.invalid",
                            },
                            method="POST",
                        )
                        with self.assertRaises(HTTPError) as cross_origin:
                            urlopen(cross_origin_request)
                        self.assertEqual(cross_origin.exception.code, 403)
                        self.assertEqual(source_path.read_text(encoding="utf-8"), original)

                        request = Request(
                            base_url + "/api/text-edit/save",
                            data=payload,
                            headers={
                                "Content-Type": "application/json",
                                "Origin": base_url,
                            },
                            method="POST",
                        )
                        with urlopen(request) as response:
                            self.assertEqual(response.status, 200)

                    updated = source_path.read_text(encoding="utf-8")
                    _, updated_body, suffix = serveur_preview._split_text_edit_section(updated)
                    self.assertIn("Texte modifié.", html.unescape(updated_body))
                    self.assertIn("| Valeur protégée |", updated_body)
                    self.assertIn("NOTE_INTERNE", updated)
                    self.assertEqual(suffix, "")
                    self.assertIn("## Section suivante\nContenu intact.", updated_body)

                    with urlopen(base_url + "/") as response:
                        preview_html = response.read().decode("utf-8")
                    self.assertIn("Texte modifié.", html.unescape(preview_html))
                    self.assertNotIn("Texte initial.", preview_html)
                    self.assertIn('<div class="manual-edit">', preview_html)
                    self.assertIn("<table>", preview_html)
                    self.assertIn("Valeur protégée", preview_html)
                finally:
                    httpd.shutdown()
                    httpd.server_close()
                    thread.join(timeout=5)

    def test_assembler_keeps_only_the_manual_edit_comments(self):
        source_script = Path(serveur_preview.__file__).with_name("assembler_markdown.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script_dir = root / "09_scripts"
            source_dir = root / "03_chapitres"
            script_dir.mkdir()
            source_dir.mkdir()
            shutil.copyfile(source_script, script_dir / "assembler_markdown.py")
            (root / "build_config.yml").write_text(
                "project:\n"
                "  title: Test bulletin\n"
                "  output_dir: 10_output\n"
                "outputs:\n"
                "  working_markdown: 10_output/travail.md\n"
                "  publication_markdown: 10_output/publication.md\n"
                "sections:\n"
                "  - title: Section test\n"
                "    files:\n"
                "      - 03_chapitres/test.md\n",
                encoding="utf-8",
            )
            (source_dir / "test.md").write_text(
                "# Test\n"
                "<!-- NOTE_INTERNE\nNe pas publier\n-->\n"
                "## Texte rédigé\n\n"
                "<!-- MANUEL_EDIT:DEBUT -->\nTexte modifié.\n"
                "<!-- MANUEL_EDIT:FIN -->\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script_dir / "assembler_markdown.py"),
                 "--preview-markdown", str(root / "preview.md")],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            publication = (root / "10_output" / "publication.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(serveur_preview.MANUAL_EDIT_START, publication)
            self.assertIn(serveur_preview.MANUAL_EDIT_END, publication)
            self.assertNotIn("NOTE_INTERNE", publication)
            preview = (root / "preview.md").read_text(encoding="utf-8")
            self.assertIn('data-preview-file="03_chapitres/test.md"', preview)
            self.assertNotIn("data-preview-file", publication)
            self.assertNotIn("Ne pas publier", preview)

