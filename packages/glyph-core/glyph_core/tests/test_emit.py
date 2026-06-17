"""Phase 2: policy evaluation + emit chains/signs/appends; denials verify GREEN."""
from __future__ import annotations

from glyph_core import emit_receipt, gen_keypair, policy, read_jsonl, verify_ledger


def test_policy_allow():
    d = policy.evaluate(4999, "acme-saas")
    assert d["decision"] == "allow"


def test_policy_deny_not_allowlisted():
    d = policy.evaluate(500, "unknown-vendor")
    assert d["decision"] == "deny"
    assert "allowlist" in d["result_detail"]


def test_policy_deny_over_limit():
    d = policy.evaluate(50000, "acme-saas")
    assert d["decision"] == "deny"
    assert "per_tx_limit" in d["result_detail"]


def test_emit_chains_and_verifies(tmp_path):
    priv, _ = gen_keypair()
    led = tmp_path / "ledger.jsonl"

    r0 = emit_receipt(
        {"amount": 4999, "merchant": "acme-saas"},
        priv_hex=priv, agent_id="a", ledger_path=led,
    )
    r1 = emit_receipt(
        {"amount": 8000, "merchant": "shady-vendor"},  # denied
        priv_hex=priv, agent_id="a", ledger_path=led,
    )
    r2 = emit_receipt(
        {"amount": 1200, "merchant": "openrouter"},
        priv_hex=priv, agent_id="a", ledger_path=led,
    )

    # chaining
    assert [r0["seq"], r1["seq"], r2["seq"]] == [0, 1, 2]
    assert r1["prev_hash"] == r0["payload_hash"]
    assert r2["prev_hash"] == r1["payload_hash"]

    # the denied spend is recorded as a deny but is still a valid signed event
    assert r1["policy"]["decision"] == "deny"
    assert r1["action"]["stripe_ref"] is None

    # whole ledger (including the deny) verifies GREEN
    results = verify_ledger(read_jsonl(led))
    assert all(r["ok"] for r in results)
