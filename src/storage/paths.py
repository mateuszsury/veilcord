"""
Application data paths for Veilcord.

All user data is stored in %APPDATA%/Veilcord/ on Windows.
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
        Path to %APPDATA%/Veilcord/

    Raises:
        OSError: If APPDATA environment variable is not set
    """
    appdata = os.getenv('APPDATA')
    if not appdata:
        raise OSError("APPDATA environment variable is not set")

    app_dir = Path(appdata) / 'Veilcord'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_db_path() -> Path:
    """
    Get the path to the SQLCipher database file.

    The database stores identity and contact information.
    It is encrypted with a key stored in db.key.

    Returns:
        Path to %APPDATA%/Veilcord/data.db
    """
    return get_app_data_dir() / 'data.db'


def get_key_path() -> Path:
    """
    Get the path to the DPAPI-encrypted database key file.

    This file contains the 32-byte encryption key for SQLCipher,
    encrypted with Windows DPAPI (user scope).

    Returns:
        Path to %APPDATA%/Veilcord/db.key
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
        Path to %APPDATA%/Veilcord/identity.key
    """
    return get_app_data_dir() / 'identity.key'


def get_data_dir() -> Path:
    """
    Get the application data directory (alias for get_app_data_dir).

    Used by file storage for encrypted file persistence.

    Returns:
        Path to %APPDATA%/Veilcord/
    """
    return get_app_data_dir()


def get_voice_messages_dir() -> Path:
    """
    Get the directory for voice message recordings.

    Voice messages are stored as Opus-encoded .ogg files.
    This directory is created if it doesn't exist.

    Returns:
        Path to %APPDATA%/Veilcord/voice_messages/
    """
    voice_dir = get_app_data_dir() / 'voice_messages'
    voice_dir.mkdir(parents=True, exist_ok=True)
    return voice_dir


def factory_reset() -> bool:
    """
    Delete all application data (factory reset).

    This removes:
    - data.db (encrypted database with contacts, messages, settings)
    - data.db-wal, data.db-shm (SQLite WAL mode files)
    - db.key (DPAPI-encrypted database key)
    - identity.key (DPAPI-encrypted private keys)
    - files/ directory (encrypted file transfers)
    - voice_messages/ directory (voice recordings)

    Returns:
        True if reset successful, False otherwise

    Note:
        After calling this, the app should be restarted to reinitialize.
    """
    import shutil
    import time
    import gc

    # Force garbage collection to release any lingering references
    gc.collect()

    try:
        app_dir = get_app_data_dir()

        # Files to delete (including SQLite WAL mode files)
        files_to_delete = [
            app_dir / 'data.db',
            app_dir / 'data.db-wal',
            app_dir / 'data.db-shm',
            app_dir / 'db.key',
            app_dir / 'identity.key',
        ]

        # Directories to delete
        dirs_to_delete = [
            app_dir / 'files',
            app_dir / 'voice_messages',
        ]

        errors = []

        # Delete files with retry
        for file_path in files_to_delete:
            if file_path.exists():
                for attempt in range(3):
                    try:
                        file_path.unlink()
                        break
                    except PermissionError:
                        if attempt < 2:
                            time.sleep(0.3)
                        else:
                            errors.append(f"Cannot delete {file_path.name}")

        # Delete directories with retry
        for dir_path in dirs_to_delete:
            if dir_path.exists():
                for attempt in range(3):
                    try:
                        shutil.rmtree(dir_path)
                        break
                    except PermissionError:
                        if attempt < 2:
                            time.sleep(0.3)
                        else:
                            errors.append(f"Cannot delete {dir_path.name}/")

        if errors:
            print(f"Factory reset partial failure: {', '.join(errors)}")
            return False

        return True
    except Exception as e:
        print(f"Factory reset failed: {e}")
        return False
