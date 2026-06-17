# Phase 4 — Glyph Receipts inside NVIDIA NemoClaw

Run the spend → signed-receipt flow inside a NemoClaw OpenShell sandbox, with Hermes
wired to a hosted **Nemotron 3 Super 120B** endpoint. The receipt is signed *inside* the
sandbox and verified *outside* it — proving portability across the trust boundary.

## What this demonstrates

Two complementary layers:

- **NemoClaw contains, in real time.** The sandbox enforces a network egress policy. By
  default `api.stripe.com` is **blocked** (only the npm/pypi/huggingface/brew presets are
  allowed), while `pypi.org` is reachable. The runtime stops what it isn't allowed to do.
- **Glyph proves, after the fact.** A receipt signed by an ephemeral key *inside* the
  sandbox verifies GREEN on the host, with no trust in the sandbox or the runtime.

## Setup (host)

```bash
# 1. Onboard Hermes in NemoClaw, routed to hosted Nemotron (non-interactive).
curl -fsSL https://www.nvidia.com/nemoclaw.sh | \
  NEMOCLAW_AGENT=hermes \
  NEMOCLAW_NON_INTERACTIVE=1 \
  NEMOCLAW_ACCEPT_THIRD_PARTY_SOFTWARE=1 \
  NEMOCLAW_PROVIDER=build \
  NEMOCLAW_MODEL=nvidia/nemotron-3-super-120b-a12b \
  NEMOCLAW_PROVIDER_KEY="$NVIDIA_API_KEY" \
  bash
# If a previous onboarding session is half-finished: `nemohermes onboard --fresh`.

nemohermes hermes status     # Phase: Ready, Inference: healthy
```

Notes:
- The provider key env var is `NEMOCLAW_PROVIDER_KEY` (the installer also accepts
  `NVIDIA_API_KEY` as an alias depending on version). The docs' `NVIDIA_INFERENCE_API_KEY`
  is not honored by every release.
- NemoClaw recognizes Docker Desktop, Colima, containerd, podman, lima, rancher — **not**
  Apple's `container`. The OpenShell gateway needs a Docker-API runtime.

## Run glyph inside the sandbox

```bash
CID=$(docker ps -q --filter name=openshell-hermes)

# Install the glyph CLI inside the sandbox (pulls glyph-protocol + cryptography
# through NemoClaw's allowed pypi egress).
docker cp packages/glyph-core "$CID:/root/glyph-core"
docker exec "$CID" pip3 install --break-system-packages /root/glyph-core

# Sign spends inside the sandbox (mock mode — Stripe egress is blocked by policy,
# which is itself the point). 2 allow + 1 deny.
docker exec "$CID" sh -lc '
  cd /root && glyph keygen >/dev/null && rm -f ledger.jsonl
  glyph spend --amount 4999 --merchant acme-saas    --ledger ledger.jsonl
  glyph spend --amount 1200 --merchant openrouter   --ledger ledger.jsonl
  glyph spend --amount 8000 --merchant shady-vendor --ledger ledger.jsonl'   # denied

# Extract and verify on the host — independent of the sandbox.
docker cp "$CID:/root/ledger.jsonl" /tmp/nemoclaw_ledger.jsonl
glyph verify /tmp/nemoclaw_ledger.jsonl     # all GREEN
```

A real Stripe charge from inside the sandbox additionally requires widening the egress
policy to allow `api.stripe.com` and providing a `sk_test_...` key inside the container.
The real test-mode path is already proven on the host in Phase 3; inside NemoClaw we keep
mock mode so no secret enters the sandbox.

## Manage

```bash
nemohermes hermes status
nemohermes hermes connect           # terminal into the sandbox / agent
nemohermes hermes logs --follow
```
