"""`glyph` CLI — keygen and verify (emit lands in Phase 2)."""
from __future__ import annotations

import argparse
import sys

from . import keys, ledger
from .emit import emit_receipt
from .stripe_spend import stripe_spend
from .verify import verify_ledger

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def cmd_keygen(args: argparse.Namespace) -> int:
    priv, pub = keys.gen_keypair()
    path = keys.save_keypair(priv, pub, args.out) if args.out else keys.save_keypair(priv, pub)
    print(f"{GREEN}✓{RESET} keypair written to {BOLD}{path}{RESET}")
    print(f"  pubkey: {pub}")
    return 0


def cmd_emit(args: argparse.Namespace) -> int:
    priv, _ = keys.load_keypair(args.key) if args.key else keys.load_keypair()
    spend = {
        "amount": args.amount,
        "merchant": args.merchant,
        "currency": args.currency,
        "stripe_ref": args.ref,
        "description": args.description,
    }
    receipt = emit_receipt(spend, priv_hex=priv, agent_id=args.agent, ledger_path=args.ledger)
    decision = receipt["policy"]["decision"]
    color = GREEN if decision == "allow" else "\033[33m"  # amber for deny
    print(
        f"{color}● {decision.upper()}{RESET}  seq {receipt['seq']}  "
        f"${args.amount / 100:.2f} → {args.merchant}  {DIM}{receipt['policy']['result_detail']}{RESET}"
    )
    print(f"  appended to {BOLD}{args.ledger}{RESET}")
    return 0


AMBER = "\033[33m"


def cmd_spend(args: argparse.Namespace) -> int:
    priv, _ = keys.load_keypair(args.key) if args.key else keys.load_keypair()
    receipt, status = stripe_spend(
        amount=args.amount,
        merchant=args.merchant,
        description=args.description,
        currency=args.currency,
        priv_hex=priv,
        agent_id=args.agent,
        ledger_path=args.ledger,
    )
    decision = receipt["policy"]["decision"]
    ref = receipt["action"]["stripe_ref"]
    if decision == "allow":
        tag = f"{GREEN}● ALLOW{RESET}"
        charge = f"  stripe {DIM}{ref}{RESET} ({status})"
    else:
        tag = f"{AMBER}● DENY{RESET}"
        charge = f"  {DIM}{receipt['policy']['result_detail']} — no charge{RESET}"
    print(f"{tag}  seq {receipt['seq']}  ${args.amount / 100:.2f} → {args.merchant}{charge}")
    print(f"  appended to {BOLD}{args.ledger}{RESET}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    receipts = ledger.read_jsonl(args.path)
    if not receipts:
        print(f"{RED}no receipts found in {args.path}{RESET}")
        return 1

    results = verify_ledger(receipts)
    all_ok = True
    print(f"{BOLD}Verifying {len(results)} receipt(s) in {args.path}{RESET}\n")
    for r, rec in zip(results, receipts):
        amount = rec.get("action", {}).get("amount")
        merchant = rec.get("action", {}).get("merchant", "?")
        meta = f"{DIM}#{r['seq']:>2}  {str(amount):>6} {rec.get('action', {}).get('currency', '')}  {merchant}{RESET}"
        if r["ok"]:
            print(f"  {GREEN}● GREEN{RESET}  {meta}")
        else:
            all_ok = False
            print(f"  {RED}● RED  {RESET}  {meta}")
            print(f"          {RED}↳ {r['failed_check']}: {r['detail']}{RESET}")

    print()
    if all_ok:
        print(f"{GREEN}{BOLD}✓ ledger intact — all receipts verify.{RESET}")
        return 0
    print(f"{RED}{BOLD}✗ ledger tampered — see RED receipt(s) above.{RESET}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="glyph", description="Glyph Receipts CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_keygen = sub.add_parser("keygen", help="generate an ed25519 agent keypair")
    p_keygen.add_argument("--out", help="path to write the keypair (default ~/.glyph/agent.key)")
    p_keygen.set_defaults(func=cmd_keygen)

    p_emit = sub.add_parser("emit", help="emit a signed receipt from a spend")
    p_emit.add_argument("--amount", type=int, required=True, help="amount in cents")
    p_emit.add_argument("--merchant", required=True)
    p_emit.add_argument("--currency", default="usd")
    p_emit.add_argument("--ref", help="stripe payment reference (allowed spends)")
    p_emit.add_argument("--description", default="")
    p_emit.add_argument("--agent", default="agent-glyph", help="agent id")
    p_emit.add_argument("--ledger", default="ledger.jsonl", help="ledger .jsonl to append to")
    p_emit.add_argument("--key", help="keypair path (default ~/.glyph/agent.key)")
    p_emit.set_defaults(func=cmd_emit)

    p_spend = sub.add_parser("spend", help="charge Stripe (test mode) and emit a receipt")
    p_spend.add_argument("--amount", type=int, required=True, help="amount in cents")
    p_spend.add_argument("--merchant", required=True)
    p_spend.add_argument("--currency", default="usd")
    p_spend.add_argument("--description", default="")
    p_spend.add_argument("--agent", default="agent-glyph", help="agent id")
    p_spend.add_argument("--ledger", default="ledger.jsonl", help="ledger .jsonl to append to")
    p_spend.add_argument("--key", help="keypair path (default ~/.glyph/agent.key)")
    p_spend.set_defaults(func=cmd_spend)

    p_verify = sub.add_parser("verify", help="verify a ledger.jsonl")
    p_verify.add_argument("path", help="path to a ledger .jsonl file")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
