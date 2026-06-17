"""Phase 2 demo: simulate three agent spends (2 allow, 1 deny) → a signed,
chained ledger that the verifier shows all GREEN.

A *denied* spend is still a valid signed event: GREEN means "authentic record",
not "payment succeeded". The policy decision lives inside the receipt.

    python scripts/sim_spends.py
"""
from __future__ import annotations

import pathlib

from glyph_core import emit_receipt, public_of, read_jsonl, verify_ledger

# Reuse the throwaway demo key so the emitted ledger shares a pubkey with the seed.
DEMO_PRIV = "9d61b19deffeb4ba3f1a0c2b7e5c3a8f4d2e1b0a9c8d7e6f5a4b3c2d1e0f9a8b"

DEMO_DIR = pathlib.Path(__file__).resolve().parents[1] / "demo"
OUT = DEMO_DIR / "emitted_ledger.jsonl"

# 2 allow, 1 deny (the middle one targets a merchant that isn't allowlisted).
SPENDS = [
    {"amount": 4999, "merchant": "acme-saas", "stripe_ref": "pi_test_seat42",
     "description": "Provisioned SaaS seat to complete task #42"},
    {"amount": 8000, "merchant": "shady-data-broker",
     "description": "Tried to buy a scraped contact list"},  # deny: not allowlisted
    {"amount": 1200, "merchant": "openrouter", "stripe_ref": "pi_test_llm01",
     "description": "LLM inference credits (per-call API)"},
]


def main() -> None:
    OUT.unlink(missing_ok=True)  # fresh ledger each run

    print(f"agent pubkey: {public_of(DEMO_PRIV)}\n")
    for spend in SPENDS:
        r = emit_receipt(spend, priv_hex=DEMO_PRIV, agent_id="agent-glyph-demo", ledger_path=OUT)
        d = r["policy"]["decision"]
        tag = "ALLOW" if d == "allow" else "DENY "
        print(f"  [{tag}] seq {r['seq']}  ${spend['amount'] / 100:>7.2f} → {spend['merchant']:<18} "
              f"{r['policy']['result_detail']}")

    receipts = read_jsonl(OUT)
    results = verify_ledger(receipts)
    allow = sum(1 for r in receipts if r["policy"]["decision"] == "allow")
    deny = len(receipts) - allow
    green = all(r["ok"] for r in results)
    print(f"\nledger: {len(receipts)} receipts ({allow} allow, {deny} deny) → "
          f"{'all GREEN ✓' if green else 'FAILED ✗'}")
    print(f"wrote {OUT.relative_to(DEMO_DIR.parent)}")


if __name__ == "__main__":
    main()
