"""
Cryptographic module for DiscordOpus.

This module provides cryptographic identity management:
- Ed25519 for signing (proving identity)
- X25519 for key exchange (future encryption)
- SHA256 fingerprints for identity verification
- Argon2id password-based backup for identity recovery
"""

# Identity management
from src.crypto.identity import Identity, generate_identity

# Fingerprint utilities
from src.crypto.fingerprint import generate_fingerprint, format_fingerprint

# Backup utilities
from src.crypto.backup import (
    BackupError,
    export_backup,
    import_backup,
)

__all__ = [
    # Identity
    'Identity',
    'generate_identity',
    # Fingerprints
    'generate_fingerprint',
    'format_fingerprint',
    # Backup
    'BackupError',
    'export_backup',
    'import_backup',
]
