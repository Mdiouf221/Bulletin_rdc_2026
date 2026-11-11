import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

