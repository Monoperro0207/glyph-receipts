"""Build a signed, hash-chained receipt.

``payload_hash`` is computed with ``glyph_protocol.canonical_hash`` (JCS / RFC 8785
+ SHA-256 hex) — we do NOT reimplement canonicalization. The signature is an
ed25519 signature over that hash string.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from glyph_protocol import canonical_hash

from . import keys
from .schema import GLYPH_VERSION, core_view


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_payload_hash(receipt: dict) -> str:
    """Canonical SHA-256 (hex) of the receipt's core (everything but hash+sig)."""
    return canonical_hash(core_view(receipt))


def build_receipt(
    *,
    priv_hex: str,
    seq: int,
    prev_hash: str,
    agent_id: str,
    action: dict,
    policy: dict,
    receipt_id: str | None = None,
    timestamp: str | None = None,
) -> dict:
    """Assemble a core, hash it, sign the hash, and return the full receipt."""
    core = {
        "glyph_version": GLYPH_VERSION,
        "receipt_id": receipt_id or str(uuid.uuid4()),
        "seq": seq,
        "prev_hash": prev_hash,
        "agent": {"id": agent_id, "pubkey": keys.public_of(priv_hex)},
        "action": action,
        "policy": policy,
        "timestamp": timestamp or _now_iso(),
    }
    payload_hash = canonical_hash(core)
    signature = keys.sign(priv_hex, payload_hash)
    return {**core, "payload_hash": payload_hash, "signature": signature}
