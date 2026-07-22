"""Unit tests for collect_enrich helpers."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collect_enrich import (  # noqa: E402
    INCIDENT_DISPLAY_CAP,
    build_recent_incidents,
    create_stub_countries,
    derive_status_from_signals,
    load_uscirf_index,
)


class TestDeriveStatus(unittest.TestCase):
    def test_opendoors_score_bands(self):
        od = {"countries": {"Nigeria": {"score": 85}}}
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("severe", "Extreme"),
        )
        od["countries"]["Nigeria"]["score"] = 65
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("severe", "Very High"),
        )
        od["countries"]["Nigeria"]["score"] = 45
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("warning", "High"),
        )
        od["countries"]["Nigeria"]["score"] = 25
        self.assertEqual(
            derive_status_from_signals("Nigeria", od, {}, {}),
            ("warning", "Moderate"),
        )

    def test_uscirf_and_acn_fallbacks(self):
        uscirf = {"Egypt": {"designation": "CPC"}}
        self.assertEqual(
            derive_status_from_signals("Egypt", {}, uscirf, {}),
            ("severe", "Extreme"),
        )
        uscirf = {"Egypt": {"designation": "SWL"}}
        self.assertEqual(
            derive_status_from_signals("Egypt", {}, uscirf, {}),
            ("warning", "High"),
        )
        acn = {"countries": {"Egypt": {"classification": "Persecution"}}}
        self.assertEqual(
            derive_status_from_signals("Egypt", {}, {}, acn),
            ("persecution", "High"),
        )


class TestBuildRecentIncidents(unittest.TestCase):
    def test_cap_and_newest_first(self):
        news = {
            "morningstarnews": {
                "countries": {
                    "Nigeria": [
                        {
                            "title": "Older church attack",
                            "url": "https://example.com/old",
                            "date": "2024-01-01",
                            "description": "Christians attacked",
                            "source": "Morning Star News",
                        },
                        {
                            "title": "Newer church attack",
                            "url": "https://example.com/new",
                            "date": "2025-06-01",
                            "description": "Christians attacked",
                            "source": "Morning Star News",
                        },
                    ]
                }
            }
        }
        # Pad with unique URLs past the display cap
        for i in range(INCIDENT_DISPLAY_CAP + 5):
            news["morningstarnews"]["countries"]["Nigeria"].append({
                "title": f"Incident {i}",
                "url": f"https://example.com/i{i}",
                "date": f"2024-02-{(i % 28) + 1:02d}",
                "description": "Church destroyed",
                "source": "Morning Star News",
            })
        incidents = build_recent_incidents("Nigeria", news)
        self.assertLessEqual(len(incidents), INCIDENT_DISPLAY_CAP)
        self.assertEqual(incidents[0]["title"], "Newer church attack")


class TestCreateStubCountries(unittest.TestCase):
    def test_creates_stub_for_known_geo_only(self):
        stubs = create_stub_countries(
            existing=[{"title": "Nigeria"}],
            sources={},
            feed_titles={"Kenya", "Nigeria", "NotARealPlaceXYZ"},
            opendoors_data={},
            uscirf_by_title={},
            acn_data={},
            news_blobs={
                "morningstarnews": {
                    "countries": {
                        "Kenya": [{
                            "title": "Church burned in Kenya",
                            "url": "https://example.com/k",
                            "date": "2025-01-01",
                            "description": "Christians attacked",
                            "source": "Morning Star News",
                        }]
                    }
                }
            },
            freedom_house={},
            owid_data={},
            vid_data={},
            gcr_data={},
            state_dept_by_title={},
            ohchr_by_title={},
            country_polygons={},
        )
        titles = {s["title"] for s in stubs}
        self.assertIn("Kenya", titles)
        self.assertNotIn("Nigeria", titles)
        kenya = next(s for s in stubs if s["title"] == "Kenya")
        self.assertEqual(kenya["slug"], "kenya")
        self.assertIn("Auto-tracked", kenya["historical"])


class TestLoadUscirfIndex(unittest.TestCase):
    def test_corrupt_index_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "uscirf" / "index.json"
            path.parent.mkdir(parents=True)
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(load_uscirf_index(root), {})


if __name__ == "__main__":
    unittest.main()
