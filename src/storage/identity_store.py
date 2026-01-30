"""
Identity persistence with secure key storage.

Storage model:
- Private keys: DPAPI-encrypted in filesystem (%APPDATA%/DiscordOpus/identity.key)
- Public keys: Stored in SQLCipher database (for reference)

This separation ensures that database compromise doesn't expose private keys,
and filesystem compromise doesn't expose contact data.
"""

import os
import json
from typing import Optional

from src.crypto.identity import Identity, generate_identity
from src.storage.dpapi import dpapi_encrypt, dpapi_decrypt
from src.storage.paths import get_identity_key_path
from src.storage.db import get_database


def has_identity() -> bool:
    """Check if user has generated an identity."""
    return os.path.exists(get_identity_key_path())


def save_identity(identity: Identity) -> None:
    """
    Save identity to secure storage.

    Private keys are DPAPI-encrypted in filesystem.
    Public keys are stored in SQLCipher database.

    Args:
        identity: Identity object to save
    """
    # Save private keys to DPAPI-encrypted file
    private_data = {
        'ed25519_private_pem': identity.ed25519_private_pem.decode('utf-8'),
        'x25519_private_raw': identity.x25519_private_raw.hex(),
        'version': 1
    }
    private_json = json.dumps(private_data).encode('utf-8')
    encrypted_private = dpapi_encrypt(private_json)

    key_path = get_identity_key_path()
    os.makedirs(os.path.dirname(key_path), exist_ok=True)

    with open(key_path, 'wb') as f:
        f.write(encrypted_private)

    # Save public data to database
    db = get_database()
    db.execute("""
        INSERT OR REPLACE INTO identity
        (id, ed25519_public_pem, x25519_public_hex, display_name, fingerprint)
        VALUES (1, ?, ?, ?, ?)
    """, (
        identity.ed25519_public_pem.decode('utf-8'),
        identity.x25519_public_hex,
        identity.display_name,
        identity.fingerprint
    ))
    db.commit()


def load_identity() -> Optional[Identity]:
    """
    Load identity from secure storage.

    Returns:
        Identity object if exists, None otherwise
    """
    key_path = get_identity_key_path()

    if not os.path.exists(key_path):
        return None

    # Load and decrypt private keys
    with open(key_path, 'rb') as f:
        encrypted_private = f.read()

    private_json = dpapi_decrypt(encrypted_private)
    private_data = json.loads(private_json.decode('utf-8'))

    # Load public data from database
    db = get_database()
    row = db.execute("""
        SELECT ed25519_public_pem, x25519_public_hex, display_name, fingerprint
        FROM identity WHERE id = 1
    """).fetchone()

    if row is None:
        return None

    ed_public_pem, x_public_hex, display_name, fingerprint = row

    return Identity(
        ed25519_private_pem=private_data['ed25519_private_pem'].encode('utf-8'),
        ed25519_public_pem=ed_public_pem.encode('utf-8'),
        x25519_private_raw=bytes.fromhex(private_data['x25519_private_raw']),
        x25519_public_raw=bytes.fromhex(x_public_hex),
        fingerprint=fingerprint,
        display_name=display_name
    )


def update_display_name(name: str) -> None:
    """
    Update identity display name.

    Args:
        name: New display name
    """
    db = get_database()
    db.execute("UPDATE identity SET display_name = ? WHERE id = 1", (name,))
    db.commit()


def get_or_create_identity(display_name: str = "Anonymous") -> Identity:
    """
    Get existing identity or create new one.

    Args:
        display_name: Display name for new identity (ignored if exists)

    Returns:
        User's cryptographic identity
    """
    identity = load_identity()

    if identity is None:
        identity = generate_identity(display_name)
        save_identity(identity)

    return identity
