# Glyph Receipts — project rules

- Goal: win a hackathon with a 3-minute demo. **Demo-first.**
- Do NOT advance a phase until the current phase's Definition of Done is met.
- Do NOT build: a policy DSL, multi-tenancy, a database, real money, or a self-hosted model.
- Policy = hardcoded (per-transaction limit + allowlist). That's it.
- The web verifier reimplements the *logic* (the four checks) from scratch in TypeScript,
  but reuses canonicalization/hashing from `@glyphp/core` so the bytes are identical to Python.
- JSON canonicalization (JCS / RFC 8785) is mandatory on both sides.
- Stripe is always in TEST MODE.
- Before writing new code that isn't in the plan, ask.
- All repository documentation, code comments, and commit messages are written in English.

## Locked decisions (confirmed)

1. **Crypto core = reuse `glyph-protocol`.** `glyph-core` depends on the PyPI package
   `glyph-protocol` for `canonical_hash`; we add `keygen` + `sign` with `cryptography`
   (`Ed25519PrivateKey`), **not** pynacl. The web verifier reuses `@glyphp/core`.
2. **Schema = a payment receipt with a hash chain** (see `README.md` / `schema.py`).
3. **Encoding:** `pubkey` and `signature` are **hex** (not base64), to match the SDK
   primitives and keep Python↔TS byte-identical.

## Hashing / signing convention (MUST match in Python and TS)

- `CORE_FIELDS` = everything except `payload_hash` and `signature`.
- `payload_hash = canonical_hash(core)` → JCS (RFC 8785) + SHA-256 hex.
- `signature = ed25519_sign(payload_hash.encode("ascii"))`, hex output.
- Chain: `prev_hash[n] == payload_hash[n-1]`; genesis (`seq:0`) `prev_hash` = 64 zeros.

## Verifier checks (in order; report the FIRST that fails)

1. **signature** — valid signature against `agent.pubkey`.
2. **hash** — recomputed `canonical_hash(core)` == stored `payload_hash`.
3. **chain** — `prev_hash[n] == payload_hash[n-1]`.
4. **sequence** — `seq` monotonic, no gaps.

## Phase status

- **Phase 0** — `glyph-core`: schema, keys, receipt, ledger, verify, CLI. ✅
- **Phase 1** — TS web verifier, the GREEN/RED moment, cross-language guard. ✅
- **Phase 2** — `emit_receipt` from a mock spend + hardcoded policy (allow/deny). ✅
- **Phase 3** — Stripe (test mode) + Hermes skill. ✅ (real test-mode charges verified in an isolated sandbox)
- **Phase 4** — NemoClaw / Nemotron runtime. ✅ (glyph runs inside the Hermes sandbox on
  hosted Nemotron 3 Super 120B; receipts signed inside verify GREEN on the host)
- **Phase 5** — agent-to-agent verification before delivery. ✅
- **Phase 6** — polish + record.
