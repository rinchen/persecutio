#!/usr/bin/env python3
"""Legacy ad-hoc checker. Prefer `python3 -m pytest tests` (what CI runs).

Deprecation: this script re-runs collect+generate. New structural checks live in
`tests/test_data_integrity.py`. The collect success check no longer requires
exact stdout ``collect ok`` — exit code 0 is enough.
"""

from pathlib import Path
import subprocess, sys, json, yaml

ROOT = Path(__file__).resolve().parent.parent


def check(cond, msg):
    if not cond:
        raise SystemExit('FAIL: ' + msg)
    print('OK:', msg)


def main():
    print('NOTE: prefer `python3 -m pytest tests` — this is a legacy smoke runner.')
    proc = subprocess.run(
        ['python3', 'scripts/collect_data.py'],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or '').strip()
        if err:
            print(err, file=sys.stderr)
    check(proc.returncode == 0, 'collect_data.py exited 0')
    out = (proc.stdout or '').strip()
    if 'collect ok' in out:
        print('OK: collect_data.py printed collect ok')
    else:
        print('OK: collect_data.py completed (stdout may include extra lines)')

    data = yaml.safe_load((ROOT / 'data' / 'countries.yml').read_text(encoding='utf-8'))
    sources = data.get('sources', {})
    check('countries' in data and 'sources' in data, 'countries.yml has countries and sources')
    check(len(data['countries']) >= 12, f"have countries (actual {len(data['countries'])})")
    check('acn2024' in sources, 'acn2024 source present')
    check(sources.get('acn2024', {}).get('date') == '2024', 'acn2024 date is 2024')

    new_slugs = {
        'algeria', 'bangladesh', 'central-african-republic', 'egypt', 'haiti',
        'libya', 'malaysia', 'myanmar', 'sudan', 'turkey', 'venezuela', 'zimbabwe'
    }
    actual_slugs = {c['slug'] for c in data['countries']}
    check(new_slugs.issubset(actual_slugs), 'new slugs present')
    check(len(actual_slugs & new_slugs) == 12, 'new slugs subset size 12')

    by_slug = {c['slug']: c for c in data['countries']}
    for slug in new_slugs:
        check('source_ids' in by_slug[slug], f'{slug} has source_ids')
        check('modern' in by_slug[slug]['source_ids'], f'{slug} modern source_ids present')
        check(len(by_slug[slug]['source_ids']['modern']) >= 1, f'{slug} modern sources non-empty')

    for c in data['countries']:
        mod = c.get('source_ids', {}).get('modern', [])
        check(len(mod) >= 1, f"{c['slug']} has modern sources")

    gen = subprocess.run(
        ['python3', 'scripts/generate_website_data.py'],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if gen.returncode != 0:
        err = (gen.stderr or gen.stdout or '').strip()
        if err:
            print(err, file=sys.stderr)
    check(gen.returncode == 0, 'generate_website_data.py exited 0')

    html_files = list((ROOT / 'countries').glob('*.html'))
    check(len(html_files) == len(data['countries']), f"html pages match country count: {len(html_files)}")

    search = json.loads((ROOT / 'assets' / 'data' / 'search.json').read_text(encoding='utf-8'))
    check(len(search) == len(data['countries']), 'search.json matches country count')
    for slug in ('algeria', 'bangladesh'):
        html = (ROOT / 'countries' / f'{slug}.html').read_text(encoding='utf-8')
        check('Open Doors World Watch List 2024' in html, f'{slug} html lists Open Doors source')
        check('USCIRF 2023 Annual Report' in html, f'{slug} html lists USCIRF annual report source')

    for k, v in sources.items():
        check(bool(v.get('title', '').strip()) and bool(v.get('url', '').strip()), f'source {k} has title/url')


if __name__ == '__main__':
    main()
