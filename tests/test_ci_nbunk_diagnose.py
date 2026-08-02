"""Tests for CI nbunksec diagnose bech32 decode (no real secret material)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ci_nbunk_diagnose import (  # noqa: E402
    CHARSET,
    CHARSET_MAP,
    bech32_polymod,
    decode_nbunksec_meta,
)


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _convertbits(data: bytes, from_bits: int, to_bits: int, pad: bool = True) -> list[int]:
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << to_bits) - 1
    for value in data:
        acc = (acc << from_bits) | value
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (to_bits - bits)) & maxv)
    return ret


def bech32_encode(hrp: str, data: bytes) -> str:
    values = _convertbits(data, 8, 5)
    checksum_values = values + [0, 0, 0, 0, 0, 0]
    polymod = bech32_polymod(_bech32_hrp_expand(hrp) + checksum_values) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(CHARSET[v] for v in values + checksum)


def _tlv(t: int, value: bytes) -> bytes:
    if len(value) > 255:
        raise ValueError("TLV value too long")
    return bytes([t, len(value)]) + value


def make_synthetic_nbunksec(
    *,
    pubkey: bytes,
    local_key: bytes,
    relays: list[str] | None = None,
    secret: bytes | None = None,
) -> str:
    raw = _tlv(0, pubkey) + _tlv(1, local_key)
    for relay in relays or []:
        raw += _tlv(2, relay.encode("utf-8"))
    if secret is not None:
        raw += _tlv(3, secret)
    return bech32_encode("nbunksec", raw)


class TestBech32Charset(unittest.TestCase):
    def test_bip173_charset(self):
        self.assertEqual(CHARSET, "qpzry9x8gf2tvdw0s3jn54khce6mua7l")
        self.assertEqual(len(CHARSET), 32)
        self.assertEqual(len(set(CHARSET)), 32)
        for ch in ("4", "6", "7"):
            self.assertIn(ch, CHARSET_MAP)


class TestDecodeNbunksecMeta(unittest.TestCase):
    def test_synthetic_roundtrip_includes_chars_467(self):
        pubkey = bytes(range(32))
        local_key = bytes(range(32, 64))
        secret = bytes(range(64, 96))
        relays = ["wss://relay.example/7", "wss://nos.lol"]
        encoded = make_synthetic_nbunksec(
            pubkey=pubkey,
            local_key=local_key,
            relays=relays,
            secret=secret,
        )
        self.assertTrue(encoded.startswith("nbunksec1"))
        # Ensure the payload data part exercises previously-missing charset chars.
        data_part = encoded.split("1", 1)[1]
        self.assertTrue(any(c in data_part for c in "467"))

        meta = decode_nbunksec_meta(encoded)
        self.assertEqual(meta["pubkey_prefix"], pubkey.hex()[:12])
        self.assertEqual(meta["pubkey_len"], 64)
        self.assertTrue(meta["has_local_key"])
        self.assertTrue(meta["has_secret"])
        self.assertEqual(meta["relays"], relays)

    def test_missing_local_key_raises(self):
        pubkey = bytes(range(32))
        raw = _tlv(0, pubkey)
        encoded = bech32_encode("nbunksec", raw)
        with self.assertRaises(ValueError):
            decode_nbunksec_meta(encoded)


if __name__ == "__main__":
    unittest.main()
