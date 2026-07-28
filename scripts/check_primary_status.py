#!/usr/bin/env python3
"""Fail CI when primary fetch status files are missing or degraded.

Primary sources must report ``ok``. ``failed``, ``partial``, and ``cached``
all abort generate/deploy so nightly cannot ship fallback/stale core data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FETCHED = ROOT / "data" / "fetched"

PRIMARY = frozenset(
    {
        "opendoors",
        "freedomhouse",
        "owid",
        "uscirf",
        "statedepartment",
    }
)
# Accept only a clean live success for primaries.
ALLOWED = frozenset({"ok"})


def check_primary_statuses(fetched_dir: Path | None = None) -> list[str]:
    """Return human-readable failure lines (empty if all primaries ok)."""
    base = fetched_dir or FETCHED
    failures: list[str] = []
    seen: set[str] = set()

    if not base.is_dir():
        return [f"missing fetched dir: {base}"]

    for p in sorted(base.glob("*_status.json")):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            name = p.stem.replace("_status", "")
            if name in PRIMARY:
                failures.append(f"{p.name}: corrupt ({type(e).__name__}: {e})")
            continue
        name = s.get("name") or p.stem.replace("_status", "")
        if name not in PRIMARY:
            continue
        seen.add(name)
        status = s.get("status")
        if status not in ALLOWED:
            msg = s.get("message") or status or "unknown"
            failures.append(f"{name}: {msg}")

    for name in sorted(PRIMARY - seen):
        failures.append(f"{name}: missing status file")

    return failures


def main() -> int:
    failures = check_primary_statuses()
    if failures:
        print("Failed primary sources:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("Primary source status files ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
