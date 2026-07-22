"""Shared helpers for scripts/fetch_*.py."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FETCHED = DATA / "fetched"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_MAX_BYTES = 20 * 1024 * 1024  # 20 MiB

KNOWN_COUNTRIES = [
    "Afghanistan", "Algeria", "Azerbaijan", "Bahrain", "Bangladesh",
    "Bhutan", "Brazil", "Brunei", "Burkina Faso", "Cameroon",
    "Central African Republic", "China", "Colombia", "Comoros", "Cuba",
    "Democratic Republic of Congo", "Egypt", "Eritrea", "Ethiopia",
    "Guinea", "Haiti", "India", "Indonesia", "Iran", "Iraq", "Jordan",
    "Kazakhstan", "Kyrgyzstan", "Laos", "Libya", "Malaysia", "Maldives",
    "Mali", "Mauritania", "Mexico", "Morocco", "Mozambique", "Myanmar",
    "Nicaragua", "Niger", "Nigeria", "North Korea", "Oman", "Pakistan",
    "Philippines", "Qatar", "Russia", "Saudi Arabia", "Somalia",
    "Sri Lanka", "Sudan", "Syria", "Tajikistan", "Tunisia", "Turkey",
    "Turkmenistan", "Uganda", "United States", "Uzbekistan", "Venezuela",
    "Vietnam", "Yemen", "Zimbabwe",
]

CHRISTIAN_TERMS = [
    "christian", "church", "pastor", "believer", "faith",
    "evangelical", "catholic", "protestant", "orthodox",
    "gospel", "jesus", "christ", "bible", "worship",
]

PERSECUTION_TERMS = [
    "persecution", "persecuted", "violence", "attack",
    "killed", "murdered", "imprisoned", "detained",
    "arrested", "harassment", "intimidation", "threat",
    "discrimination", "blasphemy", "forced conversion",
    "church closure", "church demolition", "church attack",
    "burned", "burnt", "destroyed", "vandalism",
    "religious freedom", "freedom of religion",
]


def ensure_fetched_dir() -> Path:
    FETCHED.mkdir(parents=True, exist_ok=True)
    return FETCHED


def write_status(name: str, status: str, message: str | None = None, path: Path | None = None) -> Path:
    ensure_fetched_dir()
    status_path = path or (FETCHED / f"{name}_status.json")
    payload = {
        "name": name,
        "status": status,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "message": message,
    }
    status_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return status_path


def exit_for_status(status: str) -> None:
    """Exit non-zero when the fetch logically failed."""
    if status == "failed":
        sys.exit(1)
    sys.exit(0)


def fetch_bytes(
    url: str,
    *,
    timeout: int = 30,
    max_bytes: int = DEFAULT_MAX_BYTES,
    user_agent: str = USER_AGENT,
) -> tuple[bytes | None, str | None]:
    """Fetch URL body with size cap. Returns (data, error)."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            length = resp.headers.get("Content-Length")
            if length is not None:
                try:
                    if int(length) > max_bytes:
                        return None, f"content-length {length} exceeds max {max_bytes}"
                except ValueError:
                    pass
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    return None, f"response exceeded max {max_bytes} bytes"
                chunks.append(chunk)
            return b"".join(chunks), None
    except Exception as e:
        return None, f"{type(e).__name__}"


def fetch_text(
    url: str,
    *,
    timeout: int = 30,
    max_bytes: int = DEFAULT_MAX_BYTES,
    user_agent: str = USER_AGENT,
) -> tuple[str | None, str | None]:
    data, err = fetch_bytes(url, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent)
    if err:
        print(f"  fetch error: {err}")
        return None, err
    assert data is not None
    return data.decode("utf-8", errors="replace"), None


def strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_countries(text: str, aliases: dict[str, str] | None = None) -> list[str]:
    found: list[str] = []
    text_lower = text.lower()
    for country in KNOWN_COUNTRIES:
        if re.search(r"\b" + re.escape(country.lower()) + r"\b", text_lower):
            found.append(country)
    if aliases:
        for alias, canonical in aliases.items():
            if re.search(r"\b" + re.escape(alias.lower()) + r"\b", text_lower):
                if canonical not in found:
                    found.append(canonical)
    return found


def is_persecution_article(text: str) -> bool:
    text_lower = text.lower()
    has_christian = any(t in text_lower for t in CHRISTIAN_TERMS)
    has_persecution = any(t in text_lower for t in PERSECUTION_TERMS)
    return has_christian and has_persecution


def load_json_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"  warning: corrupt cache {path.name}: {type(e).__name__}")
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_fetched_dir()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
