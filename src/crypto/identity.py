"""
Cryptographic identity management using Ed25519 and X25519 curves.

Ed25519: Signing key pair for identity verification
- Used to sign messages proving they came from you
- Public key serves as your unique identifier

X25519: Key exchange pair for encryption
- Used to establish shared secrets with contacts
- Enables end-to-end encrypted communication (Phase 3)

IMPORTANT: We generate SEPARATE Ed25519 and X25519 keys.
Do NOT convert Ed25519 to X25519 - cryptography library removed this support.
"""

from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization

from src.crypto.fingerprint import generate_fingerprint


@dataclass
class Identity:
    """User's cryptographic identity."""

    # Ed25519 signing keys (PEM format for human-readable storage)
    ed25519_private_pem: bytes
    ed25519_public_pem: bytes

    # X25519 key exchange keys (raw bytes - 32 bytes each)
    x25519_private_raw: bytes
    x25519_public_raw: bytes

    # Derived values
    fingerprint: str
    display_name: str = "Anonymous"

    @property
    def ed25519_public_hex(self) -> str:
        """Get Ed25519 public key as hex for sharing."""
        key = serialization.load_pem_public_key(self.ed25519_public_pem)
        return key.public_bytes_raw().hex()

    @property
    def x25519_public_hex(self) -> str:
        """Get X25519 public key as hex."""
        return self.x25519_public_raw.hex()

    @property
    def shareable_id(self) -> str:
        """
        Get shareable identity string (Ed25519 public key).

        This is what users share to add each other as contacts.
        """
        return self.ed25519_public_hex

    @property
    def ed25519_private_key(self) -> ed25519.Ed25519PrivateKey:
        """Get Ed25519 private key object for signing operations."""
        return serialization.load_pem_private_key(
            self.ed25519_private_pem,
            password=None
        )


def generate_identity(display_name: str = "Anonymous") -> Identity:
    """
    Generate new cryptographic identity.

    Creates:
    - Ed25519 key pair for signing
    - X25519 key pair for key exchange
    - SHA256 fingerprint for verification

    Args:
        display_name: User's display name

    Returns:
        Identity object with all keys and metadata
    """
    # Generate Ed25519 signing key pair
    ed_private = ed25519.Ed25519PrivateKey.generate()
    ed_public = ed_private.public_key()

    # Serialize Ed25519 keys to PEM format
    ed_private_pem = ed_private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()  # DPAPI handles encryption
    )
    ed_public_pem = ed_public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Generate X25519 key exchange pair
    x_private = x25519.X25519PrivateKey.generate()
    x_public = x_private.public_key()

    # X25519 keys as raw bytes (32 bytes each)
    x_private_raw = x_private.private_bytes_raw()
    x_public_raw = x_public.public_bytes_raw()

    # Generate fingerprint from Ed25519 public key
    fingerprint = generate_fingerprint(ed_public)

    return Identity(
        ed25519_private_pem=ed_private_pem,
        ed25519_public_pem=ed_public_pem,
        x25519_private_raw=x_private_raw,
        x25519_public_raw=x_public_raw,
        fingerprint=fingerprint,
        display_name=display_name
    )
