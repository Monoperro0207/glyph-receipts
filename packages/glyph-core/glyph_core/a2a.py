"""Agent-to-agent settlement: a counterparty verifies a receipt before delivering.

A provider trusts neither the buyer nor its runtime. Before handing over a
service it checks that the presented Glyph Receipt is authentic (signature),
untampered (hash), records an actual payment (policy allow), and authorizes this
provider for at least the price. Only then is the service delivered.

This is the settlement primitive an x402 / HermesHub-style exchange would call.
"""
from __future__ import annotations

from .verify import verify_receipt


def settle(receipt: dict, *, expected_merchant: str, min_amount: int) -> tuple[bool, str]:
    """Return ``(delivered, reason)``.

    Delivers only if the receipt is cryptographically intact and actually
    authorizes a paid transaction with ``expected_merchant`` for >= ``min_amount``.
    """
    # 1. Cryptographic integrity: signature + payload_hash. Pass the receipt's
    #    own prev_hash/seq so the ledger-position checks are no-ops — a single
    #    presented receipt is judged on authenticity, not its place in a ledger.
    ok, check, detail = verify_receipt(
        receipt,
        prev_payload_hash=receipt.get("prev_hash", ""),
        expected_seq=receipt.get("seq"),
    )
    if not ok:
        return False, f"rejected — receipt failed {check} check ({detail})"

    action = receipt.get("action", {})
    policy = receipt.get("policy", {})

    # 2. It must record an actual payment, not a denied attempt.
    if policy.get("decision") != "allow":
        return False, f"rejected — receipt records a '{policy.get('decision')}' decision, no payment"

    # 3. It must authorize THIS provider for at least the price.
    if action.get("merchant") != expected_merchant:
        return False, f"rejected — receipt pays '{action.get('merchant')}', not '{expected_merchant}'"
    if action.get("amount", 0) < min_amount:
        return False, f"rejected — receipt pays {action.get('amount')}, below price {min_amount}"

    return True, "service delivered"
