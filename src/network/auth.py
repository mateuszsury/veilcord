"""
Ed25519 authentication helpers for signaling server.

Challenge-response authentication flow:
1. Server sends random challenge bytes
2. Client signs challenge with Ed25519 private key
3. Server verifies signature against client's public key
"""

import base64
from cryptography.hazmat.primitives.asymmetric import ed25519


def create_auth_response(
    challenge: bytes,
    private_key: ed25519.Ed25519PrivateKey
) -> dict:
    """
    Create authentication response by signing challenge.

    Args:
        challenge: Random bytes from server to sign
        private_key: Ed25519 private key for signing

    Returns:
        JSON-serializable dict with type, public_key, and signature (base64 encoded)
    """
    # Sign the challenge
    signature = private_key.sign(challenge)

    # Get public key bytes for verification
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes_raw()

    return {
        "type": "auth_response",
        "public_key": base64.b64encode(public_key_bytes).decode('ascii'),
        "signature": base64.b64encode(signature).decode('ascii')
    }


def verify_challenge(
    challenge: bytes,
    signature_b64: str,
    public_key_b64: str
) -> bool:
    """
    Verify a challenge-response signature.

    Args:
        challenge: Original challenge bytes
        signature_b64: Base64-encoded signature
        public_key_b64: Base64-encoded Ed25519 public key

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        signature = base64.b64decode(signature_b64)
        public_key_bytes = base64.b64decode(public_key_b64)

        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, challenge)
        return True
    except Exception:
        return False
