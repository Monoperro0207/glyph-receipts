# Hermes skill: glyph-receipts

A Hermes skill that makes the agent route every spend through `glyph spend`, so each
payment produces a signed, hash-chained Glyph Receipt.

## Install

The skill is the `SKILL.md` in this directory. Make it discoverable by Hermes by copying
it into a skill folder Hermes scans (a category dir under the agent's skills tree):

```bash
# adjust the destination to your Hermes skills location
mkdir -p ~/.hermes/skills/payments/glyph-receipts
cp SKILL.md ~/.hermes/skills/payments/glyph-receipts/
```

Then make sure the `glyph` CLI is installed and a key exists:

```bash
pip install -e ../glyph-core            # provides `glyph`
glyph keygen                            # ~/.glyph/agent.key
export STRIPE_API_KEY=sk_test_...       # test key; omit to run in mock mode
```

Verify the skill is enabled with `hermes skills`. From then on, when a task requires
spending, Hermes calls `glyph spend ...` and the ledger grows with verifiable receipts.

## Demo without Hermes

The skill just wraps the CLI, so you can reproduce the exact flow by hand:

```bash
glyph spend --amount 4999 --merchant acme-saas --ledger ledger.jsonl
glyph spend --amount 8000 --merchant shady-vendor --ledger ledger.jsonl   # denied
glyph verify ledger.jsonl
```
