"""The hardcoded spend policy: a per-transaction limit + a merchant allowlist.

Deliberately not a DSL or a config system — one policy, evaluated in code. A
denied spend is still a real, signed event: the receipt records the *attempt* and
the *decision*, so the audit trail shows the policy did its job.
"""
from __future__ import annotations

POLICY_ID = "default-v1"
PER_TX_LIMIT = 10000  # cents ($100.00)
ALLOWLIST = {"acme-saas", "openrouter", "serpapi", "render-cloud", "twilio"}

# Listed in the order they are checked (mirrored in the receipt's rules_evaluated).
RULES = [f"per_tx_limit<={PER_TX_LIMIT}", "merchant_in_allowlist"]


def evaluate(amount: int, merchant: str) -> dict:
    """Return the ``policy`` block to embed in a receipt (allow or deny)."""
    if amount > PER_TX_LIMIT:
        decision, detail = "deny", f"amount {amount} exceeds per_tx_limit {PER_TX_LIMIT}"
    elif merchant not in ALLOWLIST:
        decision, detail = "deny", f"merchant '{merchant}' not in allowlist"
    else:
        decision, detail = "allow", "ok"

    return {
        "policy_id": POLICY_ID,
        "decision": decision,
        "rules_evaluated": list(RULES),
        "result_detail": detail,
    }
