import json
import subprocess
import sys
import unittest

import yaml
from pathlib import Path


ROOT = Path('/Users/joey/repos/persecutio')
DATA = ROOT / 'data'
COUNTRIES = ROOT / 'countries'
ASSETS = ROOT / 'assets' / 'data'


class TestSiteCore(unittest.TestCase):
    def test_countries_yml_has_countries(self):
        with (DATA / 'countries.yml').open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        self.assertIsInstance(data.get('countries'), list)
        self.assertTrue(data.get('countries'))

    def test_sources_yml_has_sources(self):
        with (DATA / 'sources.yml').open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        self.assertIsInstance(data.get('sources'), dict)
        self.assertTrue(data.get('sources'))

    def test_generator_produces_outputs(self):
        subprocess.run([sys.executable, str(ROOT / 'scripts/collect_data.py')], check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / 'scripts/generate_website_data.py')], check=True, cwd=ROOT)

        html_pages = sorted(COUNTRIES.glob('*.html'))
        self.assertTrue(html_pages)

        geo = json.loads((ASSETS / 'geojson.json').read_text(encoding='utf-8'))
        self.assertEqual(len(html_pages), len(geo['features']))

        search = json.loads((ASSETS / 'search.json').read_text(encoding='utf-8'))
        slugs = [p.stem for p in html_pages]
        self.assertEqual(len(search), len(slugs))
        self.assertEqual({d['slug'] for d in search}, set(slugs))

    def test_generated_pages_have_sections(self):
        pages = sorted(COUNTRIES.glob('*.html'))
        self.assertTrue(pages)
        for page in pages:
            text = page.read_text(encoding='utf-8')
            self.assertIn('Historical Background', text)
            self.assertIn('Modern-Day Situation', text)
            self.assertIn('All References</h2>', text)
            self.assertIn('href="http', text)


if __name__ == '__main__':
    unittest.main()
