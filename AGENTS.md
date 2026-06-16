# Reglas del proyecto Glyph Receipts

- Objetivo: ganar un hackathon con un demo de 3 min. **Demo-first.**
- NO avances de fase hasta cumplir el Definition of Done de la actual.
- NO construyas: DSL de políticas, multi-tenant, DB, dinero real, self-host de modelo.
- Política = hardcodeada (límite por tx + allowlist). Punto.
- El verificador web se reimplementa en TS (la *lógica* de los 4 chequeos), pero la
  canonicalización/hash se reusa de `@glyphp/core` para garantizar bytes idénticos a Python.
- Canonicalización JSON obligatoria (JCS / RFC 8785) en AMBOS lados.
- Stripe siempre en TEST MODE.
- Antes de escribir código nuevo no listado en el plan, pregunta.

## Decisiones congeladas (confirmadas)

1. **Crypto core = reusar `glyph-protocol`.** `glyph-core` depende del paquete PyPI
   `glyph-protocol` para `canonical_hash`; agregamos `keygen` + `sign` con `cryptography`
   (`Ed25519PrivateKey`), **no** pynacl. El verificador web reusa `@glyphp/core`.
2. **Schema = recibo de pago con cadena por hash** (ver `README.md` / `schema.py`).
3. **Encoding:** `pubkey` y `signature` en **hex** (no base64), para igualar las
   primitivas del SDK y mantener Python↔TS byte-idéntico.

## Convención de hashing / firma (DEBE coincidir en Python y TS)

- `CORE_FIELDS` = todo menos `payload_hash` y `signature`.
- `payload_hash = canonical_hash(core)`  → JCS (RFC 8785) + SHA-256 hex.
- `signature = ed25519_sign(payload_hash.encode("ascii"))`, salida hex.
- Cadena: `prev_hash[n] == payload_hash[n-1]`; génesis (`seq:0`) `prev_hash` = 64 ceros.

## Chequeos del verificador (en orden; reporta el PRIMERO que falle)

1. **signature** — firma válida contra `agent.pubkey`.
2. **hash** — `canonical_hash(core)` recalculado == `payload_hash` guardado.
3. **chain** — `prev_hash[n] == payload_hash[n-1]`.
4. **sequence** — `seq` monótono, sin huecos.
