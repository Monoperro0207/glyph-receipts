"""Emit a receipt from a (mock) spend: evaluate policy, sign, chain, append.

In Phase 2 the ``spend`` is a hand-built dict. In Phase 3 the same function is
fed real data captured around a Stripe (test-mode) call.
"""
from __future__ import annotations

from pathlib import Path

from . import ledger, policy
from .receipt import build_receipt
from .schema import GENESIS_PREV_HASH


def emit_receipt(
    spend: dict,
    *,
    priv_hex: str,
    agent_id: str,
    ledger_path: Path | str,
) -> dict:
    """Evaluate policy on ``spend``, build+sign a receipt chained to the last one
    in ``ledger_path``, append it, and return it.

    ``spend`` keys: ``amount`` (int, cents) and ``merchant`` (str) are required;
    ``type``, ``currency``, ``stripe_ref``, ``description`` are optional.
    """
    last = ledger.last_receipt(ledger_path)
    seq = last["seq"] + 1 if last else 0
    prev_hash = last["payload_hash"] if last else GENESIS_PREV_HASH

    decision = policy.evaluate(spend["amount"], spend["merchant"])

    action = {
        "type": spend.get("type", "stripe.payment"),
        "amount": spend["amount"],
        "currency": spend.get("currency", "usd"),
        "merchant": spend["merchant"],
        # A denied spend never reached Stripe, so it has no charge reference.
        "stripe_ref": spend.get("stripe_ref"),
        "description": spend.get("description", ""),
    }

    receipt = build_receipt(
        priv_hex=priv_hex,
        seq=seq,
        prev_hash=prev_hash,
        agent_id=agent_id,
        action=action,
        policy=decision,
    )
    ledger.append_jsonl(ledger_path, receipt)
    return receipt
