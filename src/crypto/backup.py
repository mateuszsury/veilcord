"""
Password-based key backup using Argon2id and ChaCha20-Poly1305.

DPAPI-encrypted keys are tied to the Windows user account and cannot be
recovered if Windows is reinstalled. This module provides password-based
backup for identity recovery.

Security model:
1. User provides password
2. Argon2id derives 32-byte encryption key (memory-hard, resists GPU attacks)
3. ChaCha20-Poly1305 encrypts key material (authenticated encryption)
4. Backup includes salt, nonce, and KDF parameters for decryption

Argon2id parameters (RFC 9106 recommended for desktops):
- memory_cost: 65536 (64 MB)
- iterations: 3
- lanes: 4
- key length: 32 bytes

These parameters provide strong protection while completing in <1 second.
"""

import os
import json

from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

from src.crypto.identity import Identity


class BackupError(Exception):
    """Error during backup export or import."""
    pass


# Argon2id parameters (RFC 9106 recommended)
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_ITERATIONS = 3
ARGON2_LANES = 4
ARGON2_KEY_LENGTH = 32

# Current backup format version
BACKUP_VERSION = 1


def _derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive encryption key from password using Argon2id.

    Args:
        password: User's password
        salt: Random 32-byte salt

    Returns:
        32-byte encryption key
    """
    return hash_secret_raw(
        secret=password.encode('utf-8'),
        salt=salt,
        time_cost=ARGON2_ITERATIONS,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_LANES,
        hash_len=ARGON2_KEY_LENGTH,
        type=Type.ID  # Argon2id
    )


def export_backup(identity: Identity, password: str) -> str:
    """
    Export identity as password-protected backup.

    Args:
        identity: Identity to backup
        password: Password for encryption (min 8 characters recommended)

    Returns:
        JSON string containing encrypted backup

    Raises:
        BackupError: If backup creation fails
    """
    if len(password) < 4:
        raise BackupError("Password too short (minimum 4 characters)")

    try:
        # Generate random salt and nonce
        salt = os.urandom(32)
        nonce = os.urandom(12)  # 96-bit nonce for ChaCha20-Poly1305

        # Derive encryption key from password
        encryption_key = _derive_key(password, salt)

        # Prepare key material for encryption
        key_data = json.dumps({
            'ed25519_private_pem': identity.ed25519_private_pem.decode('utf-8'),
            'ed25519_public_pem': identity.ed25519_public_pem.decode('utf-8'),
            'x25519_private_raw': identity.x25519_private_raw.hex(),
            'x25519_public_raw': identity.x25519_public_raw.hex(),
            'fingerprint': identity.fingerprint,
            'display_name': identity.display_name
        }).encode('utf-8')

        # Encrypt with ChaCha20-Poly1305 (authenticated encryption)
        cipher = ChaCha20Poly1305(encryption_key)
        ciphertext = cipher.encrypt(nonce, key_data, None)

        # Create backup structure
        backup = {
            'version': BACKUP_VERSION,
            'kdf': 'argon2id',
            'kdf_params': {
                'memory_cost': ARGON2_MEMORY_COST,
                'iterations': ARGON2_ITERATIONS,
                'lanes': ARGON2_LANES
            },
            'salt': salt.hex(),
            'nonce': nonce.hex(),
            'ciphertext': ciphertext.hex()
        }

        return json.dumps(backup, indent=2)

    except Exception as e:
        raise BackupError(f"Failed to create backup: {e}") from e


def import_backup(backup_json: str, password: str) -> Identity:
    """
    Import identity from password-protected backup.

    Args:
        backup_json: JSON string from export_backup()
        password: Password used during export

    Returns:
        Restored Identity object

    Raises:
        BackupError: If import fails (wrong password, corrupted backup, etc.)
    """
    try:
        backup = json.loads(backup_json)
    except json.JSONDecodeError as e:
        raise BackupError("Invalid backup file format") from e

    # Version check
    version = backup.get('version')
    if version != BACKUP_VERSION:
        raise BackupError(f"Unsupported backup version: {version}")

    # KDF check
    if backup.get('kdf') != 'argon2id':
        raise BackupError(f"Unsupported KDF: {backup.get('kdf')}")

    try:
        # Extract components
        salt = bytes.fromhex(backup['salt'])
        nonce = bytes.fromhex(backup['nonce'])
        ciphertext = bytes.fromhex(backup['ciphertext'])

        # Re-derive encryption key
        kdf_params = backup['kdf_params']
        encryption_key = hash_secret_raw(
            secret=password.encode('utf-8'),
            salt=salt,
            time_cost=kdf_params['iterations'],
            memory_cost=kdf_params['memory_cost'],
            parallelism=kdf_params['lanes'],
            hash_len=ARGON2_KEY_LENGTH,
            type=Type.ID
        )

        # Decrypt
        cipher = ChaCha20Poly1305(encryption_key)
        try:
            plaintext = cipher.decrypt(nonce, ciphertext, None)
        except Exception:
            raise BackupError("Wrong password or corrupted backup")

        # Parse key data
        key_data = json.loads(plaintext.decode('utf-8'))

        return Identity(
            ed25519_private_pem=key_data['ed25519_private_pem'].encode('utf-8'),
            ed25519_public_pem=key_data['ed25519_public_pem'].encode('utf-8'),
            x25519_private_raw=bytes.fromhex(key_data['x25519_private_raw']),
            x25519_public_raw=bytes.fromhex(key_data['x25519_public_raw']),
            fingerprint=key_data['fingerprint'],
            display_name=key_data['display_name']
        )

    except BackupError:
        raise
    except Exception as e:
        raise BackupError(f"Failed to import backup: {e}") from e
