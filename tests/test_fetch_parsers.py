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
from fetch_opendoors import (  # noqa: E402
    normalize_wwl_country_name,
    parse_uk_wwl_rankings,
    parse_wwl_scores_text,
)


class TestFetchCommon(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(strip_html("<p>Hello <b>world</b></p>"), "Hello world")

    def test_detect_countries(self):
        found = detect_countries("Attacks in Nigeria and India continue")
        self.assertIn("Nigeria", found)
        self.assertIn("India", found)

    def test_detect_countries_ignores_pronoun_us(self):
        self.assertNotIn(
            "United States",
            detect_countries(
                'RUSSIA: "Without any investigation, they\'re already presuming us guilty"'
            ),
        )
        self.assertNotIn(
            "United States",
            detect_countries("attacks make us complicit in the violence"),
        )
        self.assertNotIn("United States", detect_countries("Please contact us for help"))

    def test_detect_countries_matches_us_country_codes(self):
        self.assertIn("United States", detect_countries("Christians attacked in the US"))
        self.assertIn("United States", detect_countries("church burned in USA"))
        self.assertIn("United States", detect_countries("U.S. State Department report"))
        self.assertIn(
            "United States",
            detect_countries("Pastor living in the United States faces pressure"),
        )

    def test_detect_countries_ignores_english_car(self):
        self.assertNotIn(
            "Central African Republic",
            detect_countries("a car bomb kills Christians near the church"),
        )
        self.assertIn(
            "Central African Republic",
            detect_countries("militia attacks church in CAR"),
        )
        self.assertIn(
            "Central African Republic",
            detect_countries("violence in Central African Republic"),
        )

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


class TestOpenDoorsWwlParsers(unittest.TestCase):
    SAMPLE_PDF_TEXT = """
    World Watch List 2026 – countries scoring 50+ points
    1 North Korea 16.667 16.667 16.667 16.667 16.667 13.889 97 1 98 -0.5
    2 Somalia 16.667 16.667 16.667 16.667 16.667 11.111 94 2 94 0.4
    3 Yemen 16.667 16.667 16.667 16.667 16.667 9.815 93 3 94 -0.7
    4 Sudan 14.062 14.183 15.451 15.972 16.094 16.667 92 5 90 2.4
    5 Eritrea 14.583 14.904 15.465 15.885 15.899 13.333 90 6 89 1.1
    6 Syria 14.583 14.583 14.263 15.104 14.909 16.111 90 18 78 12.0
    7 Nigeria 13.542 14.103 14.583 14.909 14.792 16.667 89 7 88 0.6
    8 Pakistan 13.438 13.862 14.984 15.039 12.969 16.296 87 8 87 -0.6
    9 Libya 16.042 15.865 15.946 16.211 16.354 6.111 87 4 91 -4.8
    10 Iran 14.896 14.583 13.462 15.951 16.51 11.111 87 9 86 0.2
    11 Afghanistan 15.625 16.506 15.865 16.406 16.667 4.815 86 10 85 0.5
    12 India 12.396 13.141 13.221 15.104 13.646 16.111 84 11 84 -0.1
    13 Saudi Arabia 15.208 15.451 14.904 15.82 16.612 4.259 82 12 81 1.2
    14 Myanmar 12.708 11.458 13.221 14.258 12.969 16.296 81 13 81 0.2
    15 Mali 11.146 10.069 14.663 12.986 15.241 16.667 81 14 80 1.1
    16 Burkina Faso 11.667 9.722 13.542 13.802 14.896 16.111 80 20 76 4.1
    17 China 13.438 9.549 12.981 15.833 16.118 11.111 79 15 78 1.1
    18 Iraq 14.167 14.423 14.343 14.909 13.906 7.222 79 17 78 1.4
    19 Maldives 15.833 15.865 14.583 16.146 16.51 0.0 79 16 79 0.0
    20 Algeria 14.271 14.103 11.538 14.479 14.505 4.259 77 19 77 0.0
    21 Mauritania 14.583 14.263 13.462 14.271 14.844 3.704 76 23 75 1.0
    22 Central African Republic 10.0 9.0 12.0 11.0 13.0 16.0 75 24 74 1.0
    23 Morocco 13.229 13.802 11.298 12.917 14.375 9.259 75 21 74 0.7
    24 Cuba 13.229 8.654 13.862 13.346 15.052 9.259 73 26 73 0.4
    25 Uzbekistan 14.0 13.0 12.0 14.0 15.0 2.0 72 27 72 0.0
    26 Niger 11.0 10.0 13.0 12.0 14.0 12.0 72 28 72 0.0
    27 Tajikistan 14.0 12.0 13.0 14.0 15.0 1.0 72 30 71 1.0
    28 Laos 12.0 11.0 12.0 13.0 14.0 4.0 72 33 71 1.0
    29 Congo DR (DRC) 8.021 7.86 13.889 11.111 14.525 16.111 72 35 70 1.7
    30 Mexico 11.667 8.974 12.5 11.849 11.042 15.37 71 31 71 0.7
    31 Tunisia 12.0 11.0 12.0 13.0 14.0 3.0 71 34 70 1.0
    32 Nicaragua 11.0 10.0 12.0 13.0 14.0 5.0 71 37 69 2.0
    33 Bangladesh 12.0 11.0 12.0 13.0 14.0 4.0 71 38 69 2.0
    34 Bhutan 13.229 13.141 12.26 14.128 14.271 3.519 71 36 69 1.3
    35 Turkmenistan 14.0 12.0 13.0 14.0 15.0 1.0 71 39 68 3.0
    36 Ethiopia 10.0 9.0 12.0 11.0 12.0 14.0 70 40 68 2.0
    37 Cameroon 9.0 8.0 11.0 10.0 12.0 15.0 70 41 67 3.0
    38 Oman 14.0 13.0 11.0 14.0 15.0 1.0 70 42 67 3.0
    39 Mozambique 8.0 7.0 11.0 10.0 12.0 16.0 69 43 66 3.0
    40 Kyrgyzstan 13.0 12.0 12.0 13.0 14.0 2.0 68 45 66 2.0
    41 Turkey 12.0 11.0 12.0 13.0 14.0 3.0 68 41 67 1.0
    42 Egypt 11.0 10.0 12.0 12.0 13.0 5.0 68 40 68 0.0
    43 Comoros 14.0 13.0 12.0 14.0 15.0 1.0 68 46 65 3.0
    44 Qatar 14.0 13.0 11.0 14.0 15.0 0.0 67 47 65 2.0
    45 Kazakhstan 13.0 12.0 11.0 13.0 14.0 2.0 67 48 65 2.0
    46 Nepal 11.0 10.0 12.0 12.0 13.0 5.0 67 49 64 3.0
    47 Colombia 9.0 8.0 11.0 10.0 11.0 14.0 66 50 64 2.0
    48 Chad 11.042 8.173 10.176 9.896 10.26 16.111 66 49 65 0.2
    49 Jordan 12.917 14.263 10.417 12.174 12.76 2.778 65 50 65 0.3
    50 Brunei 14.792 15.144 10.737 9.831 14.01 0.741 65 48 66 -0.6
    """

    def test_normalize_congo_dr(self):
        self.assertEqual(
            normalize_wwl_country_name("Congo DR (DRC)"),
            "Democratic Republic of Congo",
        )

    def test_parse_scores_text_top50(self):
        parsed = parse_wwl_scores_text(self.SAMPLE_PDF_TEXT)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["year"], 2026)
        self.assertEqual(len(parsed["countries"]), 50)
        self.assertEqual(parsed["countries"]["North Korea"]["ranking"], 1)
        self.assertEqual(parsed["countries"]["North Korea"]["score"], 97)
        self.assertEqual(
            parsed["countries"]["Democratic Republic of Congo"]["ranking"], 29
        )
        self.assertEqual(parsed["countries"]["Democratic Republic of Congo"]["score"], 72)

    def test_parse_scores_text_incomplete_returns_none(self):
        self.assertIsNone(
            parse_wwl_scores_text(
                "World Watch List 2026\n1 North Korea 16.667 16.667 16.667 16.667 16.667 13.889 97 1 98 -0.5"
            )
        )

    def test_parse_uk_rankings_list(self):
        items = "".join(f"<li>{name}</li>" for name in [
            "North Korea", "Somalia", "Yemen", "Sudan", "Eritrea",
            "Syria", "Nigeria", "Pakistan", "Libya", "Iran",
            "Afghanistan", "India", "Saudi Arabia", "Myanmar", "Mali",
            "Burkina Faso", "China", "Iraq", "Maldives", "Algeria",
            "Mauritania", "Central African Republic", "Morocco", "Cuba", "Uzbekistan",
            "Niger", "Tajikistan", "Laos", "DRC", "Mexico",
            "Tunisia", "Nicaragua", "Bangladesh", "Bhutan", "Turkmenistan",
            "Ethiopia", "Cameroon", "Oman", "Mozambique", "Kyrgyzstan",
            "Türkiye", "Egypt", "Comoros", "Qatar", "Kazakhstan",
            "Nepal", "Colombia", "Chad", "Jordan", "Brunei",
            "&nbsp; Extreme",
        ])
        html = f'<ul class="wwl__rankings-list">{items}</ul>'
        parsed = parse_uk_wwl_rankings(html)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["year"], 2026)
        self.assertEqual(len(parsed["countries"]), 50)
        self.assertEqual(parsed["countries"]["Turkey"]["ranking"], 41)
        self.assertEqual(
            parsed["countries"]["Democratic Republic of Congo"]["ranking"], 29
        )


if __name__ == "__main__":
    unittest.main()
