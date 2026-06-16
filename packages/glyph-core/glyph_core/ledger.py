"""Append-only ``.jsonl`` ledger — one receipt per line."""
from __future__ import annotations

import json
from pathlib import Path


def append_jsonl(path: Path | str, receipt: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(receipt) + "\n")


def read_jsonl(path: Path | str) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def last_receipt(path: Path | str) -> dict | None:
    receipts = read_jsonl(path)
    return receipts[-1] if receipts else None
