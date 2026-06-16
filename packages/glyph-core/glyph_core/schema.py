"""Receipt shape and the canonical core view.

A receipt is a plain ``dict`` (JSON-friendly). The *core* is everything that gets
hashed and signed — i.e. every field except ``payload_hash`` and ``signature``.
``CORE_FIELDS`` is the single source of truth for what enters the hash; the TS
verifier mirrors this exact list.
"""
from __future__ import annotations

GLYPH_VERSION = "1.0"

# prev_hash of the genesis receipt (seq 0).
GENESIS_PREV_HASH = "0" * 64

# Fields that constitute the signed/hashed core, in declaration order.
# (Order is irrelevant to the hash — canonical_hash sorts keys per JCS — but it
# documents the schema.)
CORE_FIELDS = [
    "glyph_version",
    "receipt_id",
    "seq",
    "prev_hash",
    "agent",
    "action",
    "policy",
    "timestamp",
]


def core_view(receipt: dict) -> dict:
    """The hashable core: the receipt minus ``payload_hash`` and ``signature``.

    Uses ``.get`` so a tampered receipt that drops a core field still produces a
    (different) hash rather than raising — the mismatch is caught by the hash check.
    """
    return {k: receipt.get(k) for k in CORE_FIELDS}
