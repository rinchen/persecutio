#!/usr/bin/env python3
"""Tests for primary status CI gate and exit_for_status strict mode."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from check_primary_status import PRIMARY, check_primary_statuses
from fetch_common import exit_for_status


class TestCheckPrimaryStatuses(unittest.TestCase):
    def _write(self, d: Path, name: str, status: str, message: str | None = None) -> None:
        payload = {"name": name, "status": status, "message": message}
        (d / f"{name}_status.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")

    def test_all_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for name in PRIMARY:
                self._write(d, name, "ok")
            self.assertEqual(check_primary_statuses(d), [])

    def test_partial_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for name in PRIMARY:
                self._write(d, name, "ok")
            self._write(d, "opendoors", "partial", "static fallback")
            fails = check_primary_statuses(d)
            self.assertTrue(any("opendoors" in f for f in fails))

    def test_missing_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self._write(d, "opendoors", "ok")
            fails = check_primary_statuses(d)
            self.assertGreaterEqual(len(fails), 4)
            self.assertTrue(any("missing" in f for f in fails))

    def test_secondary_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for name in PRIMARY:
                self._write(d, name, "ok")
            self._write(d, "gdelt", "failed")
            self.assertEqual(check_primary_statuses(d), [])


class TestExitForStatusStrict(unittest.TestCase):
    def test_failed_always_exits_1(self):
        with self.assertRaises(SystemExit) as ctx:
            exit_for_status("failed")
        self.assertEqual(ctx.exception.code, 1)

    def test_partial_ok_when_not_strict(self):
        with self.assertRaises(SystemExit) as ctx:
            exit_for_status("partial")
        self.assertEqual(ctx.exception.code, 0)

    def test_partial_fails_when_strict(self):
        with self.assertRaises(SystemExit) as ctx:
            exit_for_status("partial", strict=True)
        self.assertEqual(ctx.exception.code, 1)

    def test_ok_strict(self):
        with self.assertRaises(SystemExit) as ctx:
            exit_for_status("ok", strict=True)
        self.assertEqual(ctx.exception.code, 0)


class TestMergeStaleStatuses(unittest.TestCase):
    def test_demote_when_fresh_present(self):
        from collect_data import merge_source_statuses

        prior = [{"name": "gdelt", "status": "ok"}, {"name": "msn", "status": "ok"}]
        fresh = [{"name": "gdelt", "status": "failed", "message": "down"}]
        merged = {s["name"]: s for s in merge_source_statuses(fresh, prior)}
        self.assertEqual(merged["gdelt"]["status"], "failed")
        self.assertEqual(merged["msn"]["status"], "stale")

    def test_keep_prior_when_no_fresh(self):
        from collect_data import merge_source_statuses

        prior = [{"name": "gdelt", "status": "ok"}]
        merged = merge_source_statuses([], prior)
        self.assertEqual(merged[0]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
