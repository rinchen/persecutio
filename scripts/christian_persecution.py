"""Shared Christian-persecution relevance filter for news/incident articles."""
from __future__ import annotations

import re

CHRISTIAN_MARKERS = (
    "christian",
    "christians",
    "christianity",
    "church",
    "churches",
    "pastor",
    "pastors",
    "priest",
    "priests",
    "bible",
    "bibles",
    "gospel",
    "jesus",
    "christ",
    "evangelical",
    "evangelicals",
    "catholic",
    "catholics",
    "protestant",
    "protestants",
    "orthodox",
    "congregation",
    "congregations",
    "missionary",
    "missionaries",
    "convert to christianity",
    "christian convert",
    "house church",
    "sunday service",
    "worship service",
)

HARM_MARKERS = (
    "persecution",
    "persecuted",
    "persecute",
    "attack",
    "attacked",
    "attacks",
    "kill",
    "killed",
    "killing",
    "murder",
    "murdered",
    "martyr",
    "martyrdom",
    "arrest",
    "arrested",
    "detain",
    "detained",
    "detention",
    "imprison",
    "imprisoned",
    "prison",
    "sentence",
    "sentenced",
    "blasphemy",
    "apostasy",
    "forced conversion",
    "forced marriage",
    "church closure",
    "church closed",
    "church demolition",
    "church demolished",
    "church attack",
    "church burned",
    "burned",
    "burnt",
    "destroyed",
    "vandalism",
    "vandalized",
    "kidnap",
    "kidnapped",
    "kidnapping",
    "abduct",
    "abducted",
    "abduction",
    "harassment",
    "harassed",
    "intimidation",
    "threat",
    "threatened",
    "discrimination",
    "discriminated",
    "religious freedom",
    "freedom of religion",
    "freedom of belief",
    "raid",
    "raided",
    "torture",
    "tortured",
    "expelled",
    "expulsion",
    "banned",
    "ban on",
    "illegal to",
    "violence",
    "violent",
    "massacre",
    "bombing",
    "bombed",
)

# Clear off-topic phrases even if keywords overlap loosely
REJECT_MARKERS = (
    "football",
    "soccer",
    "cricket score",
    "stock market",
    "recipe",
    "weather forecast",
    "box office",
)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(t in text for t in terms)


def is_christian_persecution(
    title: str | None = None,
    description: str | None = None,
    categories: list[str] | None = None,
    *,
    high_trust_source: bool = False,
) -> bool:
    """Return True if the item is about Christian persecution / related harm.

    Requires both a Christian marker and a harm/restriction marker in the
    combined text (title + description + categories), unless *high_trust_source*
    is True and categories alone clearly indicate persecution coverage.
    """
    parts = [title or "", description or ""]
    if categories:
        parts.extend(categories)
    text = " ".join(parts).lower()
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return False

    if _contains_any(text, REJECT_MARKERS):
        return False

    has_christian = _contains_any(text, CHRISTIAN_MARKERS)
    has_harm = _contains_any(text, HARM_MARKERS)

    if has_christian and has_harm:
        return True

    if high_trust_source and categories:
        cat_blob = " ".join(categories).lower()
        persecution_cats = (
            "persecution",
            "religious freedom",
            "christianity",
            "apostasy",
            "blasphemy",
            "forced conversion",
            "church attack",
            "martyrdom",
            "imprisonment",
            "kidnapping",
            "church closure",
        )
        if any(c in cat_blob for c in persecution_cats) and (
            has_christian or "christian" in cat_blob or "church" in cat_blob
        ):
            return True

    return False


# Back-compat alias used by older fetchers
def is_persecution_article(text: str) -> bool:
    return is_christian_persecution(title=text, description="")
