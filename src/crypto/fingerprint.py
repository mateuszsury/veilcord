"""
SHA256 fingerprint generation for identity verification.

Fingerprints are used to verify contacts' identities out-of-band
(e.g., comparing fingerprints in person or over phone).
"""

import hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_fingerprint(public_key: ed25519.Ed25519PublicKey) -> str:
    """
    Generate SHA256 fingerprint of Ed25519 public key.

    Args:
        public_key: Ed25519 public key object

    Returns:
        Lowercase hex string of SHA256 hash (64 characters)
    """
    raw_bytes = public_key.public_bytes_raw()
    return hashlib.sha256(raw_bytes).hexdigest()


def format_fingerprint(fingerprint: str, group_size: int = 4) -> str:
    """
    Format fingerprint for human display.

    Args:
        fingerprint: 64-character hex string
        group_size: Characters per group (default 4)

    Returns:
        Formatted string like "a1b2 c3d4 e5f6 ..."
    """
    groups = [fingerprint[i:i+group_size] for i in range(0, len(fingerprint), group_size)]
    return ' '.join(groups)
