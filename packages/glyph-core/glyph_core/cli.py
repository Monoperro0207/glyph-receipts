"""`glyph` CLI — keygen and verify (emit lands in Phase 2)."""
from __future__ import annotations

import argparse
import sys

from . import keys, ledger
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

    p_verify = sub.add_parser("verify", help="verify a ledger.jsonl")
    p_verify.add_argument("path", help="path to a ledger .jsonl file")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
