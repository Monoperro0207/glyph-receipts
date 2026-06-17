# Glyph Receipts

> The cryptographic settlement layer for agents that spend money.

Every spend an agent makes through Stripe emits a **Glyph Receipt**: an ed25519-signed,
**hash-chained** receipt that an independent third party can verify without trusting the
agent or its runtime.

NemoClaw + Stripe *stop* bad actions in real time. Glyph *proves* what happened, forever,
in a portable way. It runs **on top of** the sponsors' stack — it doesn't compete with it.

## The receipt (one spend = one receipt)

```jsonc
{
  "glyph_version": "1.0",
  "receipt_id": "<uuid-v4>",
  "seq": 7,
  "prev_hash": "<payload_hash of receipt n-1; genesis seq:0 => 64 zeros>",
  "agent":  { "id": "agent-keyid", "pubkey": "<ed25519 pubkey HEX>" },
  "action": { "type": "stripe.payment", "amount": 4999, "currency": "usd",
              "merchant": "acme-saas", "stripe_ref": "pi_test_xxx",
              "description": "Provisioned SaaS seat to complete task #42" },
  "policy": { "policy_id": "default-v1", "decision": "allow",
              "rules_evaluated": ["per_tx_limit<=10000", "merchant_in_allowlist"],
              "result_detail": "ok" },
  "timestamp": "2026-06-16T14:03:22Z",
  "payload_hash": "<sha256 hex = canonical_hash(receipt WITHOUT payload_hash & signature)>",
  "signature":    "<ed25519 signature over payload_hash, HEX>"
}
```

## Verification (four checks, report the first that fails)

1. **signature** — valid signature against `agent.pubkey`.
2. **hash** — recomputed `canonical_hash(core)` == stored `payload_hash`.
3. **chain** — `prev_hash[n] == payload_hash[n-1]`.
4. **sequence** — `seq` monotonic, no gaps.

A *denied* spend is still a valid signed event: GREEN means "authentic record", not
"payment succeeded". The policy decision lives inside the receipt.

## Status

- **Phase 0** — `glyph-core` (Python): schema, keys, receipt, ledger, verify + tests. ✅
- **Phase 1** — web verifier (Next.js/TS) with the GREEN/RED moment. ✅
- **Phase 2** — `emit_receipt` from a mock spend + hardcoded policy (allow/deny). ✅
- **Phase 3** — Stripe (test mode) + Hermes skill. ✅

## Quickstart (Python)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/glyph-core
glyph keygen
glyph emit --amount 4999 --merchant acme-saas --ledger ledger.jsonl   # allow
glyph emit --amount 8000 --merchant shady-vendor --ledger ledger.jsonl # deny (not allowlisted)
glyph verify ledger.jsonl                                              # all GREEN
```

## Quickstart (web verifier)

```bash
cd packages/glyph-verify-web
npm install
npm run dev        # http://localhost:3000
# Use the demo buttons, or drag in demo/seed_ledger.jsonl.
# Edit one amount in demo/tamper_ledger.jsonl and re-drop it -> RED.
```

## Reuse

- Python: [`glyph-protocol`](https://pypi.org/project/glyph-protocol/) → `canonical_hash`
  (JCS / RFC 8785, conformance-tested).
- TS: [`@glyphp/core`](https://www.npmjs.com/package/@glyphp/core) → `canonicalHash`
  (same canonicalization, verified byte-for-byte against Python).

## Layout

```
packages/glyph-core/        Python: schema, keys, receipt, ledger, verify, emit, policy, CLI
packages/glyph-verify-web/  Next.js + TS independent verifier (the GREEN/RED UI)
packages/hermes-skill/      Hermes skill that wraps Stripe spends and emits receipts
demo/                       seed / tampered / emitted ledgers
scripts/                    seed + spend-simulation generators
```
