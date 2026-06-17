"""Execute a spend in Stripe TEST MODE and emit a Glyph Receipt for it.

Policy is evaluated first. A denied spend never touches Stripe — it still emits a
signed receipt that records the denial. An allowed spend creates a real test-mode
PaymentIntent and the receipt carries the real Stripe reference.

Set ``STRIPE_API_KEY`` to a ``sk_test_...`` key to hit Stripe. Live keys are
rejected — this project never moves real money. Without a key (or without the
``stripe`` package) the charge falls back to a clearly-marked mock reference so
the end-to-end flow stays demoable offline.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from . import policy
from .emit import emit_receipt


def _mock_ref() -> str:
    return f"pi_test_mock_{uuid.uuid4().hex[:16]}"


def _charge(amount: int, currency: str, description: str) -> tuple[str, str]:
    """Create a test-mode PaymentIntent; return ``(stripe_ref, status)``.

    Falls back to a mock reference (status ``"mock"``) when no key/SDK is present.
    """
    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        return _mock_ref(), "mock"
    if key.startswith("sk_live"):
        raise RuntimeError("refusing to use a live Stripe key — Glyph Receipts is test-mode only")

    try:
        import stripe
    except ImportError:
        return _mock_ref(), "mock"

    stripe.api_key = key
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        payment_method="pm_card_visa",  # Stripe's test card token
        confirm=True,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        description=description or "Glyph agent spend",
    )
    return intent.id, intent.status


def stripe_spend(
    *,
    amount: int,
    merchant: str,
    priv_hex: str,
    agent_id: str,
    ledger_path: Path | str,
    description: str = "",
    currency: str = "usd",
) -> tuple[dict, str | None]:
    """Evaluate policy, charge Stripe (test mode) if allowed, emit a receipt.

    Returns ``(receipt, charge_status)``. ``charge_status`` is ``None`` for a
    denied spend, ``"succeeded"`` for a real test charge, or ``"mock"`` offline.
    """
    decision = policy.evaluate(amount, merchant)

    stripe_ref: str | None = None
    charge_status: str | None = None
    if decision["decision"] == "allow":
        stripe_ref, charge_status = _charge(amount, currency, description)

    spend = {
        "amount": amount,
        "merchant": merchant,
        "currency": currency,
        "description": description,
        "stripe_ref": stripe_ref,
    }
    receipt = emit_receipt(spend, priv_hex=priv_hex, agent_id=agent_id, ledger_path=ledger_path)
    return receipt, charge_status
