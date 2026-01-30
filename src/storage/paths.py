"""
Application data paths for DiscordOpus.

All user data is stored in %APPDATA%/DiscordOpus/ on Windows.
This includes:
- data.db: SQLCipher-encrypted database with identity and contacts
- db.key: DPAPI-encrypted database encryption key
- identity.key: DPAPI-encrypted Ed25519/X25519 private keys
"""

import os
from pathlib import Path


def get_app_data_dir() -> Path:
    """
    Get the application data directory, creating it if it doesn't exist.

    Returns:
        Path to %APPDATA%/DiscordOpus/

    Raises:
        OSError: If APPDATA environment variable is not set
    """
    appdata = os.getenv('APPDATA')
    if not appdata:
        raise OSError("APPDATA environment variable is not set")

    app_dir = Path(appdata) / 'DiscordOpus'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_db_path() -> Path:
    """
    Get the path to the SQLCipher database file.

    The database stores identity and contact information.
    It is encrypted with a key stored in db.key.

    Returns:
        Path to %APPDATA%/DiscordOpus/data.db
    """
    return get_app_data_dir() / 'data.db'


def get_key_path() -> Path:
    """
    Get the path to the DPAPI-encrypted database key file.

    This file contains the 32-byte encryption key for SQLCipher,
    encrypted with Windows DPAPI (user scope).

    Returns:
        Path to %APPDATA%/DiscordOpus/db.key
    """
    return get_app_data_dir() / 'db.key'


def get_identity_key_path() -> Path:
    """
    Get the path to the DPAPI-encrypted identity keys file.

    This file contains the Ed25519 and X25519 private keys,
    encrypted with Windows DPAPI (user scope).

    Private keys are stored separately from the database for defense
    in depth - if the database is compromised, keys remain protected.

    Returns:
        Path to %APPDATA%/DiscordOpus/identity.key
    """
    return get_app_data_dir() / 'identity.key'


def get_data_dir() -> Path:
    """
    Get the application data directory (alias for get_app_data_dir).

    Used by file storage for encrypted file persistence.

    Returns:
        Path to %APPDATA%/DiscordOpus/
    """
    return get_app_data_dir()
