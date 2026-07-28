"""Tests for scripts/source_registry.py."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from source_registry import (  # noqa: E402
    SOURCES,
    SOURCES_BY_KEY,
    fetch_script_for,
    footer_groups,
    news_sources,
    primary_keys,
    secondary_keys,
    status_key_map,
)


class TestSourceRegistry(unittest.TestCase):
    def test_no_duplicate_keys(self):
        keys = [s.key for s in SOURCES]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), set(SOURCES_BY_KEY))

    def test_fetch_scripts_exist(self):
        for s in SOURCES:
            if s.tier not in ("primary", "secondary") or not s.fetch_script:
                continue
            path = SCRIPTS / s.fetch_script
            self.assertTrue(
                path.is_file(),
                f"{s.key}: missing {s.fetch_script}",
            )
            self.assertEqual(fetch_script_for(s.key), s.fetch_script)

    def test_footer_groups_match_status_map(self):
        groups = footer_groups()
        status = status_key_map()
        for key in status:
            self.assertIn(key, groups, f"status map key {key!r} missing from footer groups")
        for key in groups:
            if key == "vdem":
                continue
            self.assertIn(key, status, f"footer group {key!r} missing from status map")

    def test_news_sources_are_secondary(self):
        secondary = set(secondary_keys())
        for fetch_key, _label, _sid in news_sources():
            self.assertIn(
                fetch_key,
                secondary,
                f"news source {fetch_key!r} is not a secondary source",
            )

    def test_primary_secondary_disjoint(self):
        primary = set(primary_keys())
        secondary = set(secondary_keys())
        self.assertTrue(primary)
        self.assertTrue(secondary)
        self.assertFalse(primary & secondary)


if __name__ == "__main__":
    unittest.main()
