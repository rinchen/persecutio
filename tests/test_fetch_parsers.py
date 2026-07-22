import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_common import (  # noqa: E402
    detect_countries,
    is_persecution_article,
    merge_articles,
    strip_html,
    write_status,
)
from rss_news_fetcher import parse_rss_items  # noqa: E402
from fetch_owid import parse_csv  # noqa: E402
from fetch_state_dept import extract_christian_mentions, strip_tags  # noqa: E402
from fetch_uscirf import normalize_name  # noqa: E402


class TestFetchCommon(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(strip_html("<p>Hello <b>world</b></p>"), "Hello world")

    def test_detect_countries(self):
        found = detect_countries("Attacks in Nigeria and India continue")
        self.assertIn("Nigeria", found)
        self.assertIn("India", found)

    def test_is_persecution_article(self):
        self.assertTrue(is_persecution_article("Christian church attacked and burned"))
        self.assertFalse(is_persecution_article("Sports scores from yesterday"))

    def test_merge_articles_caps_count(self):
        existing = [
            {
                "title": f"t{i}",
                "url": f"https://example.com/{i}",
                "date": f"2024-01-{(i % 28) + 1:02d}",
                "description": "church attack",
            }
            for i in range(20)
        ]
        merged = merge_articles(existing, [], max_articles=5, max_age_days=0)
        self.assertEqual(len(merged), 5)

    def test_write_status(self, tmp_path=None):
        # write into real FETCHED dir shape via path override
        out = ROOT / "data" / "fetched" / "_test_status.json"
        try:
            write_status("testsource", "ok", "unit", path=out)
            text = out.read_text(encoding="utf-8")
            self.assertIn('"name": "testsource"', text)
            self.assertIn('"status": "ok"', text)
        finally:
            if out.exists():
                out.unlink()


class TestRssParse(unittest.TestCase):
    def test_parse_rss_items_happy_path(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <item>
            <title>Church attacked in Nigeria</title>
            <link>https://example.com/a</link>
            <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
            <description>Christians persecuted</description>
            <category>Nigeria</category>
          </item>
        </channel></rss>
        """
        articles, err = parse_rss_items(xml, source_label="Test", high_trust=True)
        self.assertIsNone(err)
        self.assertEqual(len(articles), 1)
        self.assertIn("Nigeria", articles[0]["countries"])

    def test_parse_rss_items_bad_xml(self):
        articles, err = parse_rss_items("<not>xml", source_label="Test")
        self.assertEqual(articles, [])
        self.assertIsNotNone(err)


class TestOwidParse(unittest.TestCase):
    def test_skips_bad_rows(self):
        csv_text = (
            "Entity,Code,Year,Share of the population who are Christians\n"
            "Nigeria,NGA,2020,45.5\n"
            "Bad,XXX,notayear,12\n"
            "Egypt,EGY,2021,notafloat\n"
            "Kenya,KEN,2022,50\n"
        )
        rows = parse_csv(csv_text)
        codes = {r["code"] for r in rows.values()}
        self.assertIn("NGA", codes)
        self.assertIn("KEN", codes)
        self.assertNotIn("XXX", codes)


class TestStateDeptHelpers(unittest.TestCase):
    def test_strip_tags(self):
        self.assertIn("Hello", strip_tags("<div>Hello &amp; world</div>"))

    def test_extract_christian_mentions(self):
        text = "Christians face discrimination. The church was closed. Unrelated politics."
        mentions = extract_christian_mentions(text)
        self.assertTrue(any("Christian" in m or "church" in m.lower() for m in mentions))


class TestUscirfHelpers(unittest.TestCase):
    def test_normalize_name(self):
        self.assertEqual(normalize_name("  Burma / Myanmar "), "burma / myanmar")


if __name__ == "__main__":
    unittest.main()
