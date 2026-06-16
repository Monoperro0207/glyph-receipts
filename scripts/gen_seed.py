"""Generate the demo ledgers: a valid chained seed + a tampered copy.

Deterministic (fixed demo key + fixed timestamps) so the committed files are
reproducible. The demo private key is throwaway and intentionally in-repo.

    python scripts/gen_seed.py
"""
from __future__ import annotations

import json
import pathlib

from glyph_core import build_receipt, public_of
from glyph_core.schema import GENESIS_PREV_HASH

# Throwaway demo key (NOT a real agent key — fine to commit).
DEMO_PRIV = "9d61b19deffeb4ba3f1a0c2b7e5c3a8f4d2e1b0a9c8d7e6f5a4b3c2d1e0f9a8b"

DEMO_DIR = pathlib.Path(__file__).resolve().parents[1] / "demo"
SEED = DEMO_DIR / "seed_ledger.jsonl"
TAMPER = DEMO_DIR / "tamper_ledger.jsonl"

POLICY_OK = {
    "policy_id": "default-v1",
    "decision": "allow",
    "rules_evaluated": ["per_tx_limit<=10000", "merchant_in_allowlist"],
    "result_detail": "ok",
}

# Five real-looking agent spends to complete a task.
SPENDS = [
    ("stripe.payment", 4999, "acme-saas", "pi_test_seat42", "Provisioned SaaS seat to complete task #42"),
    ("stripe.payment", 1200, "openrouter", "pi_test_llm01", "LLM inference credits (per-call API)"),
    ("stripe.payment", 300, "serpapi", "pi_test_search7", "Web search API — 1k queries"),
    ("stripe.payment", 8000, "render-cloud", "pi_test_box9", "Spun up a worker box for a batch job"),
    ("stripe.payment", 2500, "twilio", "pi_test_sms3", "Sent verification SMS to the user"),
]

TIMESTAMPS = [
    "2026-06-16T14:03:22Z",
    "2026-06-16T14:05:10Z",
    "2026-06-16T14:06:48Z",
    "2026-06-16T14:09:31Z",
    "2026-06-16T14:12:05Z",
]


def build_chain() -> list[dict]:
    receipts: list[dict] = []
    prev = GENESIS_PREV_HASH
    for i, (typ, amount, merchant, ref, desc) in enumerate(SPENDS):
        r = build_receipt(
            priv_hex=DEMO_PRIV,
            seq=i,
            prev_hash=prev,
            agent_id="agent-glyph-demo",
            receipt_id=f"demo-receipt-{i:02d}",
            timestamp=TIMESTAMPS[i],
            action={
                "type": typ,
                "amount": amount,
                "currency": "usd",
                "merchant": merchant,
                "stripe_ref": ref,
                "description": desc,
            },
            policy=dict(POLICY_OK),
        )
        receipts.append(r)
        prev = r["payload_hash"]
    return receipts


def write_jsonl(path: pathlib.Path, receipts: list[dict]) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in receipts))


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    receipts = build_chain()
    write_jsonl(SEED, receipts)

    # Tampered copy: bump the amount on receipt #2, leave payload_hash & signature
    # untouched → breaks the `hash` check on exactly that receipt.
    tampered = [dict(r, action=dict(r["action"])) for r in receipts]
    tampered[2]["action"]["amount"] = 999999
    write_jsonl(TAMPER, tampered)

    print(f"demo pubkey: {public_of(DEMO_PRIV)}")
    print(f"wrote {SEED.relative_to(DEMO_DIR.parent)} ({len(receipts)} receipts)")
    print(f"wrote {TAMPER.relative_to(DEMO_DIR.parent)} (amount tampered on seq 2)")


if __name__ == "__main__":
    main()
