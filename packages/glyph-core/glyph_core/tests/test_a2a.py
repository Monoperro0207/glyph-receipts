"""Phase 5: a provider delivers only on an authentic receipt that pays it in full."""
from __future__ import annotations

import copy

from glyph_core import emit_receipt, gen_keypair, settle

PROVIDER = "serpapi"   # an allowlisted merchant, so an honest payment is allowed
PRICE = 3000


def _receipt(tmp_path, *, amount=PRICE, merchant=PROVIDER):
    priv, _ = gen_keypair()
    return emit_receipt(
        {"amount": amount, "merchant": merchant},
        priv_hex=priv, agent_id="buyer", ledger_path=tmp_path / "l.jsonl",
    )


def test_honest_receipt_is_delivered(tmp_path):
    ok, reason = settle(_receipt(tmp_path), expected_merchant=PROVIDER, min_amount=PRICE)
    assert ok and reason == "service delivered"


def test_tampered_receipt_is_refused(tmp_path):
    r = copy.deepcopy(_receipt(tmp_path))
    r["action"]["amount"] = 1  # tamper, leave hash/signature intact
    ok, reason = settle(r, expected_merchant=PROVIDER, min_amount=PRICE)
    assert not ok and "hash" in reason


def test_underpayment_is_refused(tmp_path):
    r = _receipt(tmp_path, amount=500)
    ok, reason = settle(r, expected_merchant=PROVIDER, min_amount=PRICE)
    assert not ok and "below price" in reason


def test_wrong_provider_is_refused(tmp_path):
    r = _receipt(tmp_path, merchant="acme-saas")
    ok, reason = settle(r, expected_merchant=PROVIDER, min_amount=PRICE)
    assert not ok and "not 'serpapi'" in reason


def test_denied_receipt_is_refused(tmp_path):
    # An over-limit spend is denied by policy; it is a valid signed event but not a payment.
    r = _receipt(tmp_path, amount=999999)
    ok, reason = settle(r, expected_merchant=PROVIDER, min_amount=PRICE)
    assert not ok and "no payment" in reason
