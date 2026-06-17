---
name: glyph-receipts
description: "Emit a signed, hash-chained Glyph Receipt for every Stripe (test-mode) spend the agent makes."
version: 0.1.0
author: Glyph Protocol, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Payments, Stripe, Audit, Cryptography, Receipts, Settlement]
    related_skills: [stripe]
---

# Glyph Receipts — verifiable agent spend

Whenever you (the agent) spend money, you MUST do it through `glyph spend`. It runs the
spend in **Stripe test mode** and emits a **Glyph Receipt**: an ed25519-signed,
hash-chained record that a third party can verify without trusting you or this runtime.
This is the audit trail. A spend that doesn't go through `glyph spend` leaves no proof.

## When to use

- Any time a task requires paying for something: provisioning a SaaS seat, buying API
  credits, paying a per-call API, spinning up compute, etc.
- Use this **instead of** calling the Stripe skill directly. `glyph spend` calls Stripe
  for you and records the result.

## Prerequisites

- `pip install -e packages/glyph-core` (provides the `glyph` CLI).
- `glyph keygen` once, to create the agent keypair (`~/.glyph/agent.key`).
- `export STRIPE_API_KEY=sk_test_...` (a **test** key — live keys are rejected).
  Without a key, `glyph spend` still works against a mock reference so the flow runs offline.

## How to spend

```bash
glyph spend --amount 4999 --merchant acme-saas \
  --description "Provisioned SaaS seat to complete task #42" \
  --ledger ledger.jsonl
```

- `--amount` is in **cents**. `--merchant` must be a recognizable merchant id.
- The hardcoded policy decides allow/deny (per-transaction limit + allowlist).
  - **allow** → a real test-mode PaymentIntent is created; its id is stored in the receipt.
  - **deny** → no charge happens, but a signed receipt still records the blocked attempt.
- The receipt is appended (hash-chained) to `--ledger`.

## Verify (anyone, anytime)

```bash
glyph verify ledger.jsonl
```

Or open the web verifier (`packages/glyph-verify-web`) and drop the ledger file. Every
receipt shows GREEN when intact; tampering with any field turns that receipt RED and names
the check that broke. GREEN means "authentic record" — a denied spend is GREEN too.

## Rules

- Never bypass `glyph spend` for a payment. No receipt = no proof = not allowed.
- Never use a live Stripe key. Test mode only.
- Do not edit `ledger.jsonl` by hand; it is append-only and hash-chained.
