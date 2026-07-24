"""Generic RSS news fetcher for Christian persecution feeds."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

from christian_persecution import is_christian_persecution
from country_registry import countries_for_article
from fetch_common import (
    build_news_result,
    exit_for_status,
    fetch_text,
    load_json_cache,
    normalize_date,
    strip_html,
    write_json,
    write_status,
)


def parse_rss_items(
    xml_text: str,
    *,
    source_label: str,
    high_trust: bool = False,
    extra_filter: Callable[[str, str, list[str]], bool] | None = None,
) -> tuple[list[dict], str | None]:
    """Parse RSS/Atom items. Returns (articles, parse_error)."""
    articles: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
        return articles, f"XML parse error: {e}"

    # RSS 2.0 channel/item or Atom feed/entry
    items = root.findall(".//item")
    if not items:
        # Atom
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry") or root.findall(
            ".//a:entry", ns
        ):
            title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            link = ""
            if link_el is not None:
                link = link_el.get("href") or (link_el.text or "")
            pub = (
                entry.findtext("{http://www.w3.org/2005/Atom}published")
                or entry.findtext("{http://www.w3.org/2005/Atom}updated")
                or ""
            ).strip()
            summary = (
                entry.findtext("{http://www.w3.org/2005/Atom}summary")
                or entry.findtext("{http://www.w3.org/2005/Atom}content")
                or ""
            )
            desc = strip_html(summary)
            cats = [
                (c.get("term") or c.text or "").strip()
                for c in entry.findall("{http://www.w3.org/2005/Atom}category")
                if (c.get("term") or c.text)
            ]
            if not is_christian_persecution(
                title=title,
                description=desc,
                categories=cats,
                high_trust_source=high_trust,
            ):
                continue
            if extra_filter and not extra_filter(title, desc, cats):
                continue
            countries = countries_for_article(title, desc, cats)
            articles.append({
                "title": title,
                "url": link.strip(),
                "date": normalize_date(pub) or pub,
                "description": desc[:500],
                "countries": countries,
                "categories": cats,
                "source": source_label,
            })
        return articles, None

    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not link:
            # Some feeds put link in enclosure/guid
            guid = item.find("guid")
            if guid is not None and (guid.text or "").startswith("http"):
                link = guid.text.strip()
        pub_date = (item.findtext("pubDate") or item.findtext("date") or "").strip()
        description = (item.findtext("description") or item.findtext("content:encoded") or "").strip()
        # content:encoded with namespace
        if not description:
            for child in list(item):
                if child.tag.endswith("encoded") and child.text:
                    description = child.text
                    break
        desc_clean = strip_html(description)

        categories = []
        for cat_elem in item.findall("category"):
            cat_text = (cat_elem.text or "").strip()
            if cat_text:
                categories.append(cat_text)

        if not is_christian_persecution(
            title=title,
            description=desc_clean,
            categories=categories,
            high_trust_source=high_trust,
        ):
            continue
        if extra_filter and not extra_filter(title, desc_clean, categories):
            continue

        countries = countries_for_article(title, desc_clean, categories)
        articles.append({
            "title": title,
            "url": link,
            "date": normalize_date(pub_date) or pub_date,
            "description": desc_clean[:500],
            "countries": countries,
            "categories": categories,
            "source": source_label,
        })

    return articles, None


RSS_FEEDS = {
    "bitterwinter": {
        "source_label": "Bitter Winter",
        "rss_url": "https://bitterwinter.org/feed/",
        "high_trust": False,
    },
    "forum18": {
        "source_label": "Forum 18",
        "rss_url": "https://www.forum18.org/syndication/forum18.xml",
        "high_trust": False,
    },
    "mec": {
        "source_label": "Middle East Concern",
        "rss_url": "https://www.meconcern.org/feed/",
        "high_trust": True,
    },
    "morningstarnews": {
        "source_label": "Morning Star News",
        "rss_url": "https://morningstarnews.org/feed/",
        "high_trust": True,
    },
    "releaseintl": {
        "source_label": "Release International",
        "rss_url": "https://releaseinternational.org/feed/",
        "high_trust": True,
    },
}


def run_rss_fetcher(
    *,
    name: str,
    source_label: str | None = None,
    rss_url: str | None = None,
    output: Path | None = None,
    high_trust: bool | None = None,
) -> None:
    from fetch_common import FETCHED, ensure_fetched_dir

    ensure_fetched_dir()
    cfg = RSS_FEEDS.get(name, {})
    source_label = source_label or cfg.get("source_label") or name
    rss_url = rss_url or cfg.get("rss_url")
    if not rss_url:
        raise ValueError(f"No RSS URL configured for {name}")
    if high_trust is None:
        high_trust = bool(cfg.get("high_trust", False))
    output = output or (FETCHED / f"{name}.json")

    print(f"Fetching {source_label} RSS...")
    cached = load_json_cache(output)
    xml_text, err = fetch_text(rss_url)
    if xml_text is None:
        if cached:
            print("  fetch failed, using cached data")
            cached["status"] = "cached"
            write_json(output, cached)
            write_status(name, "cached", "fetch failed, using cache")
            exit_for_status("cached")
        result = build_news_result(
            source=source_label,
            source_url=rss_url,
            status="fetch_failed",
            articles=[],
        )
        write_json(output, result)
        write_status(name, "failed", f"fetch failed: {err}")
        exit_for_status("failed")

    articles, parse_err = parse_rss_items(
        xml_text, source_label=source_label, high_trust=high_trust
    )
    if parse_err:
        if cached:
            print(f"  {parse_err}; keeping cached data")
            cached["status"] = "partial"
            write_json(output, cached)
            write_status(name, "partial", parse_err)
            exit_for_status("partial")
        result = build_news_result(
            source=source_label,
            source_url=rss_url,
            status="parse_failed",
            articles=[],
        )
        write_json(output, result)
        write_status(name, "failed", parse_err)
        exit_for_status("failed")

    print(f"  found {len(articles)} Christian-persecution articles")
    result = build_news_result(
        source=source_label,
        source_url=rss_url,
        status="ok",
        articles=articles,
        previous=cached,
    )
    write_json(output, result)
    print(f"  wrote {output} ({result['total_articles']} accumulated)")
    write_status(name, "ok")
    exit_for_status("ok")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch a configured RSS news feed")
    parser.add_argument("name", choices=sorted(RSS_FEEDS))
    args = parser.parse_args()
    run_rss_fetcher(name=args.name)
