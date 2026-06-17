"""Phase 3: stripe_spend evaluates policy, charges (mock offline), emits a receipt."""
from __future__ import annotations

from glyph_core import gen_keypair, read_jsonl, stripe_spend, verify_ledger


def test_allowed_spend_gets_ref_and_verifies(tmp_path, monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)  # force mock charge
    priv, _ = gen_keypair()
    led = tmp_path / "ledger.jsonl"

    receipt, status = stripe_spend(
        amount=4999, merchant="acme-saas", description="seat",
        priv_hex=priv, agent_id="a", ledger_path=led,
    )
    assert receipt["policy"]["decision"] == "allow"
    assert receipt["action"]["stripe_ref"].startswith("pi_test_mock_")
    assert status == "mock"
    assert verify_ledger(read_jsonl(led))[0]["ok"]


def test_denied_spend_never_charges(tmp_path, monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    priv, _ = gen_keypair()
    led = tmp_path / "ledger.jsonl"

    receipt, status = stripe_spend(
        amount=8000, merchant="shady-vendor",
        priv_hex=priv, agent_id="a", ledger_path=led,
    )
    assert receipt["policy"]["decision"] == "deny"
    assert receipt["action"]["stripe_ref"] is None
    assert status is None
    # the denial is still a valid signed event
    assert verify_ledger(read_jsonl(led))[0]["ok"]


def test_live_key_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_live_should_never_be_used")
    priv, _ = gen_keypair()
    led = tmp_path / "ledger.jsonl"
    try:
        stripe_spend(amount=100, merchant="acme-saas", priv_hex=priv, agent_id="a", ledger_path=led)
        assert False, "expected a refusal on a live key"
    except RuntimeError as e:
        assert "live" in str(e).lower()
