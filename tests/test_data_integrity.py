"""Structural integrity checks for generated / collected site data (CI-friendly)."""
from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class TestSearchSchema(unittest.TestCase):
    def test_search_entries_have_required_keys(self):
        path = ROOT / "assets" / "data" / "search.json"
        self.assertTrue(path.exists(), "search.json missing — run generate")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 12)
        for entry in data:
            self.assertIsInstance(entry, dict)
            for key in ("slug", "title"):
                self.assertIn(key, entry, entry)
                self.assertTrue(str(entry[key]).strip(), f"empty {key} in {entry}")


class TestCitationCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        yml = ROOT / "data" / "countries.yml"
        cls.data = yaml.safe_load(yml.read_text(encoding="utf-8"))
        cls.sources = cls.data.get("sources") or {}
        cls.countries = cls.data.get("countries") or []

    def test_curated_countries_have_resolvable_modern_sources(self):
        for c in self.countries:
            if (c.get("metadata") or {}).get("stub"):
                continue
            modern = (c.get("source_ids") or {}).get("modern") or []
            self.assertTrue(modern, f"{c.get('slug')} missing modern source_ids")
            for sid in modern:
                self.assertIn(sid, self.sources, f"{c.get('slug')} cites unknown source {sid}")

    def test_no_duplicate_source_ids_within_bucket(self):
        for c in self.countries:
            ids = c.get("source_ids") or {}
            for bucket in ("modern", "historical"):
                vals = ids.get(bucket) or []
                self.assertEqual(
                    len(vals),
                    len(set(vals)),
                    f"{c.get('slug')} duplicate {bucket} source_ids: {vals}",
                )

    def test_country_count_matches_geojson_features(self):
        geo_path = ROOT / "assets" / "data" / "geojson.json"
        self.assertTrue(geo_path.exists())
        geo = json.loads(geo_path.read_text(encoding="utf-8"))
        features = geo.get("features") or []
        self.assertEqual(len(features), len(self.countries))

    def test_source_dates_not_wildly_in_future(self):
        """Soft anomaly: date year more than 1 ahead of calendar year is unexpected."""
        limit = date.today().year + 1
        anomalies = []
        for sid, meta in self.sources.items():
            raw = str((meta or {}).get("date") or "")
            if len(raw) >= 4 and raw[:4].isdigit():
                year = int(raw[:4])
                if year > limit:
                    anomalies.append((sid, year))
        # Do not hard-fail legitimate near-term report years; only absurd futures
        absurd = [(s, y) for s, y in anomalies if y > limit + 1]
        self.assertEqual(absurd, [], f"absurd future source dates: {absurd}")


if __name__ == "__main__":
    unittest.main()
