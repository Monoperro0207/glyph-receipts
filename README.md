# Glyph Receipts

> La capa de liquidación criptográfica para agentes que gastan dinero.

Cada gasto que un agente hace vía Stripe emite un **Glyph Receipt**: un recibo ed25519
firmado y **encadenado por hash**, verificable por un tercero independiente que no confía
ni en el agente ni en el runtime.

NemoClaw + Stripe *frenan* acciones malas en tiempo real. Glyph *prueba* qué pasó, para
siempre, de forma portátil. Corre **encima** del stack de los sponsors, no compite con él.

## El recibo (un gasto = un recibo)

```jsonc
{
  "glyph_version": "1.0",
  "receipt_id": "<uuid-v4>",
  "seq": 7,
  "prev_hash": "<payload_hash del recibo n-1; génesis seq:0 => 64 ceros>",
  "agent":  { "id": "agent-keyid", "pubkey": "<ed25519 pubkey HEX>" },
  "action": { "type": "stripe.payment", "amount": 4999, "currency": "usd",
              "merchant": "acme-saas", "stripe_ref": "pi_test_xxx",
              "description": "Provisioned SaaS seat to complete task #42" },
  "policy": { "policy_id": "default-v1", "decision": "allow",
              "rules_evaluated": ["per_tx_limit<=10000", "merchant_in_allowlist"],
              "result_detail": "ok" },
  "timestamp": "2026-06-16T14:03:22Z",
  "payload_hash": "<sha256 hex = canonical_hash(recibo MENOS payload_hash y signature)>",
  "signature":    "<ed25519 sign sobre payload_hash, HEX>"
}
```

## Verificación (4 chequeos, reporta el primero que falle)

1. **signature** — firma válida contra `agent.pubkey`.
2. **hash** — `canonical_hash(core)` recalculado == `payload_hash` guardado.
3. **chain** — `prev_hash[n] == payload_hash[n-1]`.
4. **sequence** — `seq` monótono, sin huecos.

## Estado

- **Fase 0** — `glyph-core` (Python): schema, keys, receipt, ledger, verify + tests. ✅
- **Fase 1** — verificador web (Next.js/TS) con el momento VERDE/ROJO. ⏳

## Quickstart (Python)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/glyph-core
glyph keygen
glyph verify demo/seed_ledger.jsonl     # todo VERDE
glyph verify demo/tamper_ledger.jsonl   # ROJO en el recibo manipulado
```

## Reuso

- Python: [`glyph-protocol`](https://pypi.org/project/glyph-protocol/) → `canonical_hash`
  (JCS / RFC 8785, conformance-tested).
- TS: [`@glyphp/core`](https://www.npmjs.com/package/@glyphp/core) → `canonicalHash`
  (misma canonicalización, verificada byte-a-byte contra Python).
