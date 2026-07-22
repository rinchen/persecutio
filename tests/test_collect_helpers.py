import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import collect_data as cd  # noqa: E402


class TestCountryPolygons(unittest.TestCase):
    def test_iso_a3_preferred(self):
        geo = {
            "features": [
                {
                    "properties": {"ISO_A3": "NGA"},
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                },
                {
                    "properties": {"ADM0_A3": "IND"},
                    "geometry": {"type": "Polygon", "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 2]]]},
                },
                {
                    "properties": {"ISO_A3": "XXX"},
                    "geometry": None,
                },
            ]
        }
        by_iso = cd.country_polygons_from_geojson(geo)
        self.assertIn("NGA", by_iso)
        self.assertIn("IND", by_iso)
        self.assertNotIn("XXX", by_iso)


class TestFetchJson(unittest.TestCase):
    def test_network_fail_uses_cache_as_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('{"ok": true}', encoding="utf-8")
            with mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
                data, status = cd.fetch_json("https://example.invalid/x", path, "sample", skip=False)
            self.assertEqual(data, {"ok": True})
            self.assertEqual(status["status"], "partial")

    def test_skip_uses_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('{"cached": 1}', encoding="utf-8")
            data, status = cd.fetch_json("https://example.invalid/x", path, "sample", skip=True)
            self.assertEqual(data, {"cached": 1})
            self.assertEqual(status["status"], "cached")

    def test_fail_without_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            with mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
                data, status = cd.fetch_json("https://example.invalid/x", path, "missing", skip=False)
            self.assertEqual(data, {})
            self.assertEqual(status["status"], "failed")


if __name__ == "__main__":
    unittest.main()
