"""Verify a ledger: four ordered checks per receipt, report the first that fails.

Check order (mirrored exactly by the TS verifier):
  1. signature — ed25519 sig valid against agent.pubkey over the stored payload_hash
  2. hash      — canonical_hash(core) recomputed == stored payload_hash
  3. chain     — prev_hash == previous receipt's payload_hash
  4. sequence  — seq is monotonic with no gaps (expected == index)
"""
from __future__ import annotations

from . import keys
from .receipt import compute_payload_hash
from .schema import GENESIS_PREV_HASH

CHECKS = ("schema", "signature", "hash", "chain", "sequence")


def verify_receipt(receipt: dict, *, prev_payload_hash: str, expected_seq: int):
    """Return ``(ok, failed_check, detail)`` for a single receipt."""
    try:
        pub = receipt["agent"]["pubkey"]
        stored_hash = receipt["payload_hash"]
        signature = receipt["signature"]
    except (KeyError, TypeError):
        return False, "schema", "receipt is missing required fields"

    # 1. signature over the stored payload_hash
    if not keys.verify_sig(pub, stored_hash, signature):
        return False, "signature", "ed25519 signature does not verify against agent.pubkey"

    # 2. content actually hashes to the stored payload_hash
    recomputed = compute_payload_hash(receipt)
    if recomputed != stored_hash:
        return (
            False,
            "hash",
            f"content hashes to {recomputed[:12]}… but receipt claims {stored_hash[:12]}…",
        )

    # 3. chain link to the previous receipt
    if receipt.get("prev_hash") != prev_payload_hash:
        return (
            False,
            "chain",
            f"prev_hash {str(receipt.get('prev_hash'))[:12]}… != previous payload_hash "
            f"{prev_payload_hash[:12]}…",
        )

    # 4. sequence monotonic, no gaps
    if receipt.get("seq") != expected_seq:
        return False, "sequence", f"seq is {receipt.get('seq')}, expected {expected_seq}"

    return True, None, "ok"


def verify_ledger(receipts: list[dict]) -> list[dict]:
    """Verify every receipt in order. Each result is a dict:
    ``{index, seq, ok, failed_check, detail}``.
    """
    results: list[dict] = []
    prev_hash = GENESIS_PREV_HASH
    for i, r in enumerate(receipts):
        ok, check, detail = verify_receipt(r, prev_payload_hash=prev_hash, expected_seq=i)
        results.append(
            {
                "index": i,
                "seq": r.get("seq", i),
                "ok": ok,
                "failed_check": check,
                "detail": detail,
            }
        )
        # Advance the chain by THIS receipt's stored hash so a single tampered
        # receipt only reddens itself, not every receipt after it.
        prev_hash = r.get("payload_hash", "")
    return results
