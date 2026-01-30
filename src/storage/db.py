"""
SQLCipher encrypted database with DPAPI-protected key.

Security model:
1. Database key (32 random bytes) is generated on first run
2. Key is encrypted with DPAPI and stored in db.key file
3. SQLCipher uses the key to encrypt/decrypt the database
4. All queries go through encrypted database - no plaintext on disk

CRITICAL: PRAGMA key MUST be the first operation after sqlite3.connect().
Any query before PRAGMA key will fail or corrupt the database.

Key storage separation:
- Database encryption key: stored in db.key (DPAPI-encrypted)
- Identity private keys: stored in identity.key (DPAPI-encrypted)
- Database contains only public keys (identity and contacts tables)

This separation means compromising the database file alone does not
expose private keys, and vice versa.
"""

import os
from typing import Optional

import sqlcipher3

from src.storage.paths import get_db_path, get_key_path
from src.storage.dpapi import dpapi_encrypt, dpapi_decrypt


# Module-level connection singleton
_db_connection: Optional[sqlcipher3.Connection] = None


def get_or_create_db_key() -> bytes:
    """
    Get existing database key or create new one.

    The key is stored DPAPI-encrypted in the filesystem.
    DPAPI encryption is tied to the Windows user account.

    On first run, a new 32-byte cryptographically random key is generated.
    On subsequent runs, the existing key is loaded and decrypted.

    Returns:
        32-byte database encryption key

    Raises:
        pywintypes.error: If DPAPI decryption fails (wrong user account)
        OSError: If key file operations fail
    """
    key_path = get_key_path()

    if key_path.exists():
        # Load and decrypt existing key
        with open(key_path, 'rb') as f:
            encrypted_key = f.read()
        return dpapi_decrypt(encrypted_key)
    else:
        # Generate new 32-byte key
        new_key = os.urandom(32)

        # Encrypt with DPAPI and save
        encrypted_key = dpapi_encrypt(new_key)

        # Ensure directory exists
        key_path.parent.mkdir(parents=True, exist_ok=True)

        with open(key_path, 'wb') as f:
            f.write(encrypted_key)

        return new_key


def init_database() -> sqlcipher3.Connection:
    """
    Initialize SQLCipher database with encryption.

    Creates database and schema if they don't exist.
    Uses DPAPI-protected key for encryption.

    The database schema includes:
    - identity: Single row with user's public keys and display name
    - contacts: List of known contacts with their public keys

    Returns:
        SQLCipher connection object

    Raises:
        sqlcipher3.DatabaseError: If key is wrong or database corrupted
        pywintypes.error: If DPAPI key decryption fails
    """
    global _db_connection

    if _db_connection is not None:
        return _db_connection

    db_key = get_or_create_db_key()
    db_path = get_db_path()

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    # check_same_thread=False: Required because PyWebView runs API methods
    # in a separate thread from where the connection was created.
    # SQLite handles its own locking internally, so this is safe.
    conn = sqlcipher3.connect(str(db_path), check_same_thread=False)

    # CRITICAL: Set key BEFORE any other operations
    conn.execute(f"PRAGMA key = \"x'{db_key.hex()}'\"")

    # Set SQLCipher 4.x compatibility
    conn.execute("PRAGMA cipher_compatibility = 4")

    # Verify key is correct (this will fail if key is wrong)
    try:
        conn.execute("SELECT count(*) FROM sqlite_master")
    except sqlcipher3.DatabaseError as e:
        conn.close()
        raise sqlcipher3.DatabaseError(
            "Failed to open database. Key may be incorrect or database corrupted."
        ) from e

    # Create schema
    # identity table: single row (enforced by CHECK constraint)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS identity (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            ed25519_public_pem TEXT NOT NULL,
            x25519_public_hex TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT 'Anonymous',
            fingerprint TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # contacts table: known peers
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ed25519_public_pem TEXT UNIQUE NOT NULL,
            x25519_public_hex TEXT NOT NULL,
            display_name TEXT NOT NULL,
            fingerprint TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            online_status TEXT DEFAULT 'unknown'
        )
    """)

    # Migration: add online_status column to existing databases
    try:
        conn.execute(
            "ALTER TABLE contacts ADD COLUMN online_status TEXT DEFAULT 'unknown'"
        )
    except sqlcipher3.OperationalError:
        pass  # Column already exists

    # settings table: key-value store for user preferences
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # messages table: P2P chat message history
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id INTEGER NOT NULL,
            sender_id TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'text',
            body TEXT,
            reply_to TEXT,
            edited INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0,
            timestamp INTEGER NOT NULL,
            received_at INTEGER,
            FOREIGN KEY (conversation_id) REFERENCES contacts(id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation
        ON messages(conversation_id, timestamp)
    """)

    # reactions table: emoji reactions to messages
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            emoji TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(id),
            UNIQUE(message_id, sender_id, emoji)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_reactions_message
        ON reactions(message_id)
    """)

    # signal_sessions table: Signal Protocol session state persistence
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signal_sessions (
            contact_id INTEGER PRIMARY KEY,
            session_state BLOB NOT NULL,
            updated_at INTEGER NOT NULL,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)

    conn.commit()

    _db_connection = conn
    return conn


def get_database() -> sqlcipher3.Connection:
    """
    Get database connection, initializing if needed.

    This is the primary entry point for database access.
    The connection is a singleton - multiple calls return the same connection.

    Returns:
        Active SQLCipher connection
    """
    global _db_connection

    if _db_connection is None:
        return init_database()

    return _db_connection


def close_database() -> None:
    """
    Close database connection.

    Call this when shutting down the application to ensure
    all changes are flushed and the connection is properly closed.
    """
    global _db_connection

    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None
