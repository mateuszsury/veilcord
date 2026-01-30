"""
Cryptographic module for DiscordOpus.

This module provides cryptographic identity management:
- Ed25519 for signing (proving identity)
- X25519 for key exchange (encryption)
- SHA256 fingerprints for identity verification
- Argon2id password-based backup for identity recovery
- Signal Protocol for E2E encrypted messaging
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
    export_backup_to_file,
    import_backup_from_file,
    get_backup_info,
)

# Signal Protocol session management
from src.crypto.signal_session import (
    SignalSession,
    EncryptedMessage,
    encrypted_message_to_dict,
    encrypted_message_from_dict,
)

# High-level message encryption API
# NOTE: message_crypto imports are deferred to avoid circular import with storage
# Import directly: from src.crypto.message_crypto import encrypt_message, ...
def __getattr__(name: str):
    """Lazy import for message_crypto to avoid circular import."""
    if name in (
        'OutgoingMessage', 'encrypt_message', 'decrypt_message',
        'encrypt_message_sync', 'decrypt_message_sync', 'has_session', 'reset_session'
    ):
        from src.crypto import message_crypto
        return getattr(message_crypto, name)
    raise AttributeError(f"module 'src.crypto' has no attribute {name!r}")

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
    'export_backup_to_file',
    'import_backup_from_file',
    'get_backup_info',
    # Signal Protocol
    'SignalSession',
    'EncryptedMessage',
    'encrypted_message_to_dict',
    'encrypted_message_from_dict',
    # Message encryption
    'OutgoingMessage',
    'encrypt_message',
    'decrypt_message',
    'encrypt_message_sync',
    'decrypt_message_sync',
    'has_session',
    'reset_session',
]
