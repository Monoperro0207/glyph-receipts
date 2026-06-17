"""Isolated sandbox that simulates how Hermes drives the glyph-receipts skill.

It NEVER touches your real environment: HOME is redirected into ./sandbox/home,
so `glyph` reads/writes its key there, the ledger lives in ./sandbox, and every
shell call the "agent" makes is logged to ./sandbox/behavior.log for monitoring.

This mirrors a Hermes skill invocation (the agent shells out to `glyph spend`)
without installing anything into your Hermes. Run in mock mode by default; set a
test key to exercise the real Stripe path:

    python scripts/sandbox_hermes.py                 # mock
    STRIPE_API_KEY=sk_test_... python scripts/sandbox_hermes.py
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
GLYPH = ROOT / ".venv" / "bin" / "glyph"
SANDBOX = ROOT / "sandbox"

# A simulated Hermes task that requires spending money:
# "Spin up what you need to finish task #42, but don't buy anything shady."
TASK_SPENDS = [
    ("4999", "acme-saas", "Provisioned SaaS seat to complete task #42"),
    ("1200", "openrouter", "Bought LLM inference credits (per-call API)"),
    ("8000", "shady-data-broker", "Attempted to buy a scraped contact list"),  # policy should deny
]


def log_line(log: pathlib.Path, text: str) -> None:
    with log.open("a") as f:
        f.write(text + "\n")
    print(text)


def run(args: list[str], env: dict, log: pathlib.Path) -> str:
    cmd = [str(GLYPH), *args]
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    log_line(log, f"\n[{ts}] $ glyph {' '.join(args)}")
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).rstrip()
    log_line(log, out)
    if proc.returncode != 0:
        log_line(log, f"  ↳ exit {proc.returncode}")
    return out


def main() -> int:
    if not GLYPH.exists():
        print(f"glyph CLI not found at {GLYPH}; run: pip install -e packages/glyph-core")
        return 1

    SANDBOX.mkdir(exist_ok=True)
    home = SANDBOX / "home"
    home.mkdir(exist_ok=True)
    keyfile = SANDBOX / "agent.key"
    ledger = SANDBOX / "ledger.jsonl"
    log = SANDBOX / "behavior.log"
    for p in (ledger, log):
        p.unlink(missing_ok=True)

    # Fully isolate: redirect HOME so no global ~/.glyph or ~/.hermes is touched.
    env = dict(os.environ)
    env["HOME"] = str(home)

    mode = "REAL Stripe test-mode" if env.get("STRIPE_API_KEY") else "MOCK (no STRIPE_API_KEY)"
    log_line(log, f"=== Hermes sandbox — charge mode: {mode} ===")
    log_line(log, f"sandbox: {SANDBOX}   (HOME redirected, your environment untouched)")

    run(["keygen", "--out", str(keyfile)], env, log)

    log_line(log, "\n--- agent works the task, spending as needed ---")
    for amount, merchant, desc in TASK_SPENDS:
        run(
            ["spend", "--amount", amount, "--merchant", merchant, "--description", desc,
             "--ledger", str(ledger), "--key", str(keyfile)],
            env, log,
        )

    log_line(log, "\n--- independent verification ---")
    run(["verify", str(ledger)], env, log)

    # Behavior summary (monitoring).
    receipts = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    log_line(log, "\n--- behavior summary ---")
    for r in receipts:
        d = r["policy"]["decision"]
        ref = r["action"]["stripe_ref"]
        kind = "real" if ref and not ref.startswith("pi_test_mock_") else ("mock" if ref else "—")
        log_line(log, f"  seq {r['seq']}  {d:<5}  {r['action']['merchant']:<18} ref={ref} [{kind}]")
    log_line(log, f"\nfull log: {log.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
