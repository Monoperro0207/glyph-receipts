"""Phase 5 demo: agent-to-agent settlement.

A buyer agent pays a provider and presents a Glyph Receipt. The provider verifies
the receipt before delivering — trusting neither the buyer nor its runtime. Tamper
the receipt and the provider refuses to deliver.

    python scripts/a2a_verify.py
"""
from __future__ import annotations

import copy
import pathlib

from glyph_core import emit_receipt, gen_keypair, settle

PROVIDER = "serpapi"    # the counterparty's merchant id (an allowlisted API provider)
PRICE = 3000            # cents ($30.00)

G = "\033[32m"
R = "\033[31m"
DIM = "\033[2m"
B = "\033[1m"
X = "\033[0m"


def deliver(label: str, receipt: dict) -> None:
    ok, reason = settle(receipt, expected_merchant=PROVIDER, min_amount=PRICE)
    mark = f"{G}✓ DELIVERED{X}" if ok else f"{R}✗ REFUSED{X}"
    print(f"  {label:<34} {mark}  {DIM}{reason}{X}")


def main() -> None:
    priv, _ = gen_keypair()
    led = pathlib.Path("/tmp/a2a_ledger.jsonl")
    led.unlink(missing_ok=True)

    # Buyer agent pays the provider for a dataset.
    paid = emit_receipt(
        {"amount": PRICE, "merchant": PROVIDER, "stripe_ref": "pi_test_x",
         "description": "Bought 1k search-API queries"},
        priv_hex=priv, agent_id="buyer-agent", ledger_path=led,
    )

    print(f"{B}Provider '{PROVIDER}' settles each request by verifying the Glyph Receipt:{X}\n")

    # 1. Honest payment → delivered.
    deliver("honest receipt", paid)

    # 2. Tampered amount (buyer edits the receipt to look like a bigger payment,
    #    or any field) → hash check fails → refused.
    tampered = copy.deepcopy(paid)
    tampered["action"]["amount"] = 1  # edit a field, leave hash/signature intact
    deliver("tampered receipt (amount edited)", tampered)

    # 3. Underpayment: a real, valid receipt but below the price → refused.
    underpaid = emit_receipt(
        {"amount": 500, "merchant": PROVIDER, "description": "underpaid"},
        priv_hex=priv, agent_id="buyer-agent", ledger_path=led,
    )
    deliver("valid receipt, underpaid ($5)", underpaid)

    # 4. Receipt for a different provider → refused.
    elsewhere = emit_receipt(
        {"amount": PRICE, "merchant": "acme-saas", "description": "paid someone else"},
        priv_hex=priv, agent_id="buyer-agent", ledger_path=led,
    )
    deliver("valid receipt, wrong provider", elsewhere)

    print(f"\n{DIM}Only an authentic, untampered receipt that actually pays this provider "
          f"gets the service.{X}")


if __name__ == "__main__":
    main()
