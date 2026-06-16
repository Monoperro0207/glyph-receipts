"""Phase 0 DoD: sign a receipt → verify GREEN; tamper one byte → RED on the right check."""
from __future__ import annotations

from glyph_core import build_receipt, gen_keypair, verify_ledger
from glyph_core.schema import GENESIS_PREV_HASH

ACTION = {
    "type": "stripe.payment",
    "amount": 4999,
    "currency": "usd",
    "merchant": "acme-saas",
    "stripe_ref": "pi_test_abc",
    "description": "Provisioned SaaS seat to complete task #42",
}
POLICY = {
    "policy_id": "default-v1",
    "decision": "allow",
    "rules_evaluated": ["per_tx_limit<=10000", "merchant_in_allowlist"],
    "result_detail": "ok",
}


def _genesis() -> tuple[str, dict]:
    priv, _ = gen_keypair()
    receipt = build_receipt(
        priv_hex=priv,
        seq=0,
        prev_hash=GENESIS_PREV_HASH,
        agent_id="agent-test",
        action=dict(ACTION),
        policy=dict(POLICY),
    )
    return priv, receipt


def test_sign_and_verify_green():
    _, receipt = _genesis()
    results = verify_ledger([receipt])
    assert results[0]["ok"] is True
    assert results[0]["failed_check"] is None


def test_tamper_amount_fails_hash():
    _, receipt = _genesis()
    receipt["action"]["amount"] = 999999  # tamper, leave payload_hash/signature intact
    results = verify_ledger([receipt])
    assert results[0]["ok"] is False
    assert results[0]["failed_check"] == "hash"


def test_chain_links_two_receipts():
    priv, first = _genesis()
    second = build_receipt(
        priv_hex=priv,
        seq=1,
        prev_hash=first["payload_hash"],
        agent_id="agent-test",
        action=dict(ACTION, amount=1200, description="API call"),
        policy=dict(POLICY),
    )
    results = verify_ledger([first, second])
    assert all(r["ok"] for r in results)


def test_broken_chain_fails_chain_check():
    priv, first = _genesis()
    second = build_receipt(
        priv_hex=priv,
        seq=1,
        prev_hash="f" * 64,  # wrong link
        agent_id="agent-test",
        action=dict(ACTION, amount=1200),
        policy=dict(POLICY),
    )
    results = verify_ledger([first, second])
    assert results[0]["ok"] is True
    assert results[1]["ok"] is False
    assert results[1]["failed_check"] == "chain"
