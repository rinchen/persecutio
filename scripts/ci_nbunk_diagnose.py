#!/usr/bin/env python3
"""Diagnose NBUNK_SECRET hygiene and bunker/deploy relay reachability for CI.

Never prints key material (local_key / shared secret). Exit 2 on permanent
credential/config errors; exit 0 when deploy may proceed (including when
bunker relays are temporarily unreachable — that is retryable).
"""

from __future__ import annotations

import json
import os
import socket
import ssl
import sys
import time
import urllib.parse

DEPLOY_RELAYS = [
    "wss://relay.nsite.lol",
    "wss://nos.lol",
    "wss://relay.nostr.band",
    "wss://relay.primal.net",
]

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
CHARSET_MAP = {c: i for i, c in enumerate(CHARSET)}


def bech32_polymod(values: list[int]) -> int:
    generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= generator[i]
    return chk


def bech32_decode(value: str) -> tuple[str, bytes]:
    value = value.strip()
    if any(ord(x) < 33 or ord(x) > 126 for x in value):
        raise ValueError("invalid bech32 characters")
    if value.lower() != value and value.upper() != value:
        raise ValueError("mixed-case bech32")
    value = value.lower()
    pos = value.rfind("1")
    if pos < 1 or pos + 7 > len(value):
        raise ValueError("invalid bech32 separator")
    hrp = value[:pos]
    data_part = value[pos + 1 :]
    try:
        data = [CHARSET_MAP[c] for c in data_part]
    except KeyError as exc:
        raise ValueError(f"invalid bech32 char: {exc}") from exc
    if bech32_polymod(
        [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp] + data
    ) != 1:
        raise ValueError("bech32 checksum failed")
    data = data[:-6]
    acc = 0
    bits = 0
    out = bytearray()
    for value5 in data:
        acc = (acc << 5) | value5
        bits += 5
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xFF)
    return hrp, bytes(out)


def decode_nbunksec_meta(nbunksec: str) -> dict:
    hrp, raw = bech32_decode(nbunksec)
    if hrp != "nbunksec":
        raise ValueError(f"unexpected prefix: {hrp}")
    offset = 0
    pubkey = ""
    has_local_key = False
    has_secret = False
    relays: list[str] = []
    while offset < len(raw):
        if offset + 2 > len(raw):
            raise ValueError("truncated TLV")
        t = raw[offset]
        length = raw[offset + 1]
        offset += 2
        if offset + length > len(raw):
            raise ValueError("truncated TLV value")
        value = raw[offset : offset + length]
        offset += length
        if t == 0:
            pubkey = value.hex()
        elif t == 1:
            has_local_key = True
        elif t == 2:
            relays.append(value.decode("utf-8"))
        elif t == 3:
            has_secret = True
        else:
            raise ValueError(f"unknown TLV type {t}")
    if not pubkey or not has_local_key:
        raise ValueError("nbunksec missing pubkey or local_key")
    return {
        "pubkey_prefix": pubkey[:12],
        "pubkey_len": len(pubkey),
        "has_local_key": has_local_key,
        "has_secret": has_secret,
        "relays": relays,
    }


def probe_wss(url: str, timeout_s: float = 8.0) -> dict:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("wss", "ws"):
        return {"url": url, "ok": False, "error": f"bad scheme {parsed.scheme}"}
    host = parsed.hostname
    if not host:
        return {"url": url, "ok": False, "error": "missing host"}
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    started = time.time()
    try:
        raw = socket.create_connection((host, port), timeout=timeout_s)
        sock = (
            ssl.create_default_context().wrap_socket(raw, server_hostname=host)
            if parsed.scheme == "wss"
            else raw
        )
        key = "dGhlIHNhbXBsZSBub25jZQ=="
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        sock.settimeout(timeout_s)
        sock.sendall(req.encode("ascii"))
        resp = sock.recv(1024).decode("latin1", errors="replace")
        sock.close()
        status_line = resp.split("\r\n", 1)[0]
        return {
            "url": url,
            "ok": "101" in status_line,
            "status_line": status_line,
            "ms": int((time.time() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001 - probe must not abort the job
        return {
            "url": url,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "ms": int((time.time() - started) * 1000),
        }


def append_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)
        if not text.endswith("\n"):
            fh.write("\n")


def main() -> int:
    raw = os.environ.get("NBUNK_SECRET", "")
    stripped = raw.strip()
    hygiene = {
        "present": bool(raw),
        "raw_len": len(raw),
        "stripped_len": len(stripped),
        "has_leading_ws": bool(raw) and raw[:1].isspace(),
        "has_trailing_ws": bool(raw) and raw[-1:].isspace(),
        "startswith_nbunksec1": stripped.startswith("nbunksec1"),
        "startswith_sec1": stripped.startswith("sec1"),
    }

    print("::group::nbunk hygiene (no secret values)")
    print(json.dumps(hygiene, indent=2))
    print("::endgroup::")

    if not stripped:
        print("::error::NBUNK_SECRET is missing or empty")
        append_summary("## Nostr diagnose\n\n- **Permanent error:** `NBUNK_SECRET` missing/empty\n")
        return 2
    if stripped.startswith("sec1"):
        print(
            "::error::NBUNK_SECRET looks like a sec1 private key. "
            "Use an nbunksec1 credential from `nsyte ci`."
        )
        append_summary("## Nostr diagnose\n\n- **Permanent error:** sec1 key (not nbunksec1)\n")
        return 2
    if not stripped.startswith("nbunksec1"):
        print("::error::NBUNK_SECRET must start with nbunksec1")
        append_summary("## Nostr diagnose\n\n- **Permanent error:** not nbunksec1 prefix\n")
        return 2
    if hygiene["has_leading_ws"] or hygiene["has_trailing_ws"]:
        print(
            "::warning::NBUNK_SECRET has leading/trailing whitespace; "
            "deploy will use a stripped copy in the retry script if exported stripped."
        )

    try:
        meta = decode_nbunksec_meta(stripped)
    except Exception as exc:  # noqa: BLE001
        print(f"::error::Failed to decode NBUNK_SECRET: {type(exc).__name__}: {exc}")
        append_summary(
            f"## Nostr diagnose\n\n- **Permanent error:** decode failed (`{type(exc).__name__}`)\n"
        )
        return 2

    bunker_relays = meta["relays"]
    overlap = sorted(set(bunker_relays) & set(DEPLOY_RELAYS))
    print("::group::nbunk bunker relays")
    print(
        json.dumps(
            {
                "pubkey_prefix": meta["pubkey_prefix"],
                "pubkey_len": meta["pubkey_len"],
                "has_local_key": meta["has_local_key"],
                "has_secret": meta["has_secret"],
                "bunker_relays": bunker_relays,
                "deploy_relays": DEPLOY_RELAYS,
                "relay_overlap": overlap,
            },
            indent=2,
        )
    )
    print("::endgroup::")

    if not bunker_relays:
        print("::warning::nbunksec has no embedded bunker relays")

    probe_targets = list(dict.fromkeys([*bunker_relays, *DEPLOY_RELAYS]))
    results = [probe_wss(url) for url in probe_targets]
    print("::group::relay websocket probes")
    print(json.dumps(results, indent=2))
    print("::endgroup::")

    bunker_results = [r for r in results if r["url"] in bunker_relays]
    any_bunker_ok = any(r.get("ok") for r in bunker_results) if bunker_results else False
    if bunker_results and not any_bunker_ok:
        print(
            "::warning::No bunker relay accepted a WebSocket upgrade from this runner. "
            "Deploy may still succeed if the bunker comes online; retries will apply."
        )

    # Expose for the retry script / later steps (non-secret).
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as fh:
            fh.write(f"NBUNK_BUNKER_RELAYS={','.join(bunker_relays)}\n")
            fh.write(f"NBUNK_PUBKEY_PREFIX={meta['pubkey_prefix']}\n")

    append_summary("## Nostr diagnose\n")
    append_summary(f"- Pubkey prefix: `{meta['pubkey_prefix']}…`")
    append_summary(
        "- Bunker relays: "
        + (", ".join(f"`{r}`" for r in bunker_relays) if bunker_relays else "(none)")
    )
    append_summary(
        "- Bunker relay WS: "
        + ("at least one OK" if any_bunker_ok else "none OK / none listed")
    )
    append_summary("- Credential: ok (nbunksec1 decoded)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
