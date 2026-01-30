"""
Cryptographic module for DiscordOpus.

This module provides cryptographic identity management:
- Ed25519 for signing (proving identity)
- X25519 for key exchange (future encryption)
- SHA256 fingerprints for identity verification
"""

# Identity management
from src.crypto.identity import Identity, generate_identity

# Fingerprint utilities
from src.crypto.fingerprint import generate_fingerprint, format_fingerprint

__all__ = [
    # Identity
    'Identity',
    'generate_identity',
    # Fingerprints
    'generate_fingerprint',
    'format_fingerprint',
]
