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
            with mock.patch("fetch_common.fetch_text", return_value=(None, "OSError: down")):
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
            with mock.patch("fetch_common.fetch_text", return_value=(None, "OSError: down")):
                data, status = cd.fetch_json("https://example.invalid/x", path, "missing", skip=False)
            self.assertEqual(data, {})
            self.assertEqual(status["status"], "failed")

    def test_bad_json_does_not_poison_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_text('{"ok": true}', encoding="utf-8")
            with mock.patch(
                "fetch_common.fetch_text",
                return_value=("<html>not json</html>", None),
            ):
                data, status = cd.fetch_json("https://example.invalid/x", path, "sample", skip=False)
            self.assertEqual(data, {"ok": True})
            self.assertEqual(status["status"], "partial")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ok": True})

    def test_valid_json_writes_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            with mock.patch(
                "fetch_common.fetch_text",
                return_value=('{"fresh": 1}', None),
            ):
                data, status = cd.fetch_json("https://example.invalid/x", path, "sample", skip=False)
            self.assertEqual(data, {"fresh": 1})
            self.assertEqual(status["status"], "ok")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["fresh"], 1)


class TestMergeSourceStatuses(unittest.TestCase):
    def test_fresh_overrides_prior(self):
        prior = [{"name": "opendoors", "status": "ok", "fetched_at": "old"}]
        fresh = [{"name": "opendoors", "status": "partial", "fetched_at": "new"}]
        merged = cd.merge_source_statuses(fresh, prior)
        self.assertEqual(merged, [{"name": "opendoors", "status": "partial", "fetched_at": "new"}])

    def test_preserves_missing_status_files(self):
        prior = [
            {"name": "opendoors", "status": "partial", "fetched_at": "nightly"},
            {"name": "freedomhouse", "status": "ok", "fetched_at": "nightly"},
            {"name": "morningstarnews", "status": "ok", "fetched_at": "old"},
        ]
        fresh = [
            {"name": "natural_earth_110m", "status": "ok", "fetched_at": "local"},
            {"name": "morningstarnews", "status": "ok", "fetched_at": "local"},
        ]
        merged = cd.merge_source_statuses(fresh, prior)
        by_name = {s["name"]: s for s in merged}
        self.assertEqual(set(by_name), {"natural_earth_110m", "morningstarnews", "opendoors", "freedomhouse"})
        self.assertEqual(by_name["opendoors"]["fetched_at"], "nightly")
        self.assertEqual(by_name["morningstarnews"]["fetched_at"], "local")

    def test_ignores_malformed_entries(self):
        merged = cd.merge_source_statuses(
            [{"name": "ok", "status": "ok"}, "bad", {"status": "ok"}],
            [None, {"name": "prior", "status": "ok"}],
        )
        self.assertEqual([s["name"] for s in merged], ["ok", "prior"])


if __name__ == "__main__":
    unittest.main()
