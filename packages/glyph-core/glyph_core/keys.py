"""ed25519 keypair generation and storage (hex), via ``cryptography``.

The Glyph Protocol SDK we reuse is verify-only, so signing/keygen lives here.
Keys are raw ed25519 bytes hex-encoded — the same encoding the SDK's verify path
expects for ``serverPublicKey``/``signature``.
"""
from __future__ import annotations

import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

DEFAULT_KEY_PATH = Path.home() / ".glyph" / "agent.key"


def gen_keypair() -> tuple[str, str]:
    """Return ``(priv_hex, pub_hex)`` for a fresh ed25519 keypair."""
    sk = Ed25519PrivateKey.generate()
    priv_hex = sk.private_bytes_raw().hex()
    pub_hex = sk.public_key().public_bytes_raw().hex()
    return priv_hex, pub_hex


def load_private(priv_hex: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(priv_hex))


def public_of(priv_hex: str) -> str:
    """Derive the hex public key from a hex private key."""
    return load_private(priv_hex).public_key().public_bytes_raw().hex()


def sign(priv_hex: str, message: str) -> str:
    """ed25519-sign an ASCII string, returning a hex signature."""
    return load_private(priv_hex).sign(message.encode("ascii")).hex()


def verify_sig(pub_hex: str, message: str, signature_hex: str) -> bool:
    """Verify a hex signature over an ASCII string against a hex public key."""
    from cryptography.exceptions import InvalidSignature

    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex)).verify(
            bytes.fromhex(signature_hex), message.encode("ascii")
        )
        return True
    except (InvalidSignature, ValueError):
        return False


def save_keypair(priv_hex: str, pub_hex: str, path: Path | str = DEFAULT_KEY_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"priv": priv_hex, "pub": pub_hex}))
    path.chmod(0o600)
    return path


def load_keypair(path: Path | str = DEFAULT_KEY_PATH) -> tuple[str, str]:
    data = json.loads(Path(path).read_text())
    return data["priv"], data["pub"]
