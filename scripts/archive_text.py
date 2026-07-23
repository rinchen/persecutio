"""Shared helpers for archived report excerpt cleanup and clipping."""
from __future__ import annotations

import re

# Prefer complete sentences; keep excerpts short for fair-use display.
DEFAULT_OD_LIMIT = 600
DEFAULT_IRF_LIMIT = 500
DEFAULT_USCIRF_LIMIT = 500
# Store enough prose in YAML for sentence-aware display clipping.
STORE_SUMMARY_LIMIT = 2000

_SENT_END = re.compile(r'[.!?…]["”\']?')


def clean_archive_text(text: str) -> str:
    """Fix common PDF/HTML letter-spacing and hyphen artifacts."""
    if not text:
        return ""
    t = str(text)
    # Known multi-letter OCR splits before generic pairwise collapse
    t = re.sub(r"\bh\s+u\s+dud\b", "hudud", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\bt\s+(hese|hat|hen|his|heir)\b",
        lambda m: "t" + m.group(1),
        t,
        flags=re.IGNORECASE,
    )
    # "non -Muslim" / "non - Muslim" → "non-Muslim"
    t = re.sub(r"(\w)\s+-\s*(\w)", r"\1-\2", t)
    # Collapse runs of spaced single letters: "a b c" → "abc", "a n" → "an"
    prev = None
    while prev != t:
        prev = t
        t = re.sub(
            r"(?<![A-Za-z])([A-Za-z]) ([A-Za-z])(?![A-Za-z])",
            r"\1\2",
            t,
        )
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_usable_archive_excerpt(text: str, *, min_len: int = 60) -> bool:
    """Reject TOC leftovers and punctuation-leading fragments."""
    t = (text or "").strip()
    if len(t) < min_len:
        return False
    if t[0] in ')"\'.,;:]' or t[0].isdigit():
        return False
    if not (t[0].isalpha() or t[0] in '"“‘«'):
        return False
    # Mid-sentence leftovers
    if re.match(r"^(and|or|but|also|which|that|who|whom)\b", t, re.I):
        return False
    # Page-header noise
    if re.search(r"Persecution Dynamics\s*[–—-]\s*\w+\s+\d{4}\s*$", t) and len(t) < 120:
        return False
    return True


def clip_at_sentence(text: str, limit: int) -> tuple[str, bool]:
    """
    Truncate at a sentence boundary when possible.

    Returns (excerpt, was_truncated). Appends an ellipsis only when falling back
    to a word boundary (no sentence end in the window).
    """
    text = clean_archive_text(text or "").strip()
    if not text:
        return "", False
    if len(text) <= limit:
        return text, False

    window = text[:limit]
    best_end = -1
    for m in _SENT_END.finditer(window):
        end = m.end()
        if end < 15:
            continue
        # Skip initials / single-letter false ends ("U.S.", " e.")
        prev = re.search(r"(\S+)$", window[: m.start()])
        if prev and len(prev.group(1).rstrip(".")) <= 1:
            continue
        # Skip abbreviation-like periods mid-token (no space after)
        if end < len(text) and not text[end].isspace():
            continue
        # Skip ". lowercase" continuations
        after = text[end : end + 8].lstrip()
        if after and after[0].islower():
            continue
        best_end = end

    if best_end > 0:
        return window[:best_end].rstrip(), True

    cut = window.rsplit(" ", 1)[0].rstrip(" ,;:-")
    return ((cut or window).rstrip() + "…"), True


def store_summary(text: str, limit: int = STORE_SUMMARY_LIMIT) -> str:
    """Clean and optionally shorten a summary for YAML storage (sentence-safe)."""
    text = clean_archive_text(text or "").strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    clipped, _ = clip_at_sentence(text, limit)
    # Prefer not storing a dangling ellipsis in YAML when we can keep a full sentence
    return clipped.rstrip("…").rstrip() if clipped.endswith("…") else clipped
