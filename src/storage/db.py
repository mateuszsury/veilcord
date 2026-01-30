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

    # files table: file metadata and content storage
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            mime_type TEXT,
            size INTEGER NOT NULL,
            hash TEXT NOT NULL,
            data BLOB,
            file_path TEXT,
            created_at INTEGER NOT NULL,
            transfer_id TEXT
        )
    """)

    # file_transfers table: file transfer state tracking
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_transfers (
            id TEXT PRIMARY KEY,
            contact_id INTEGER NOT NULL,
            direction TEXT NOT NULL,
            filename TEXT NOT NULL,
            size INTEGER NOT NULL,
            hash TEXT NOT NULL,
            bytes_transferred INTEGER DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
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


# File transfer state persistence functions

def save_transfer_state(
    transfer_id: str,
    contact_id: int,
    direction: str,
    filename: str,
    size: int,
    hash_value: str,
    bytes_transferred: int = 0,
    state: str = "pending"
) -> None:
    """
    Save or update file transfer state.

    Args:
        transfer_id: Unique transfer UUID
        contact_id: Contact database ID
        direction: "send" or "receive"
        filename: Original filename
        size: Total file size in bytes
        hash_value: SHA256 hash of file
        bytes_transferred: Bytes sent/received so far
        state: Transfer state (pending, active, complete, failed, cancelled)
    """
    import time
    conn = get_database()
    timestamp = int(time.time() * 1000)

    # Upsert: insert or update if exists
    conn.execute("""
        INSERT INTO file_transfers
        (id, contact_id, direction, filename, size, hash, bytes_transferred, state, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            bytes_transferred = excluded.bytes_transferred,
            state = excluded.state,
            updated_at = excluded.updated_at
    """, (
        transfer_id, contact_id, direction, filename, size, hash_value,
        bytes_transferred, state, timestamp, timestamp
    ))
    conn.commit()


def get_transfer_state(transfer_id: str) -> Optional[dict]:
    """
    Get transfer state by ID.

    Returns:
        Dictionary with transfer state or None if not found
    """
    conn = get_database()
    row = conn.execute("""
        SELECT id, contact_id, direction, filename, size, hash,
               bytes_transferred, state, created_at, updated_at
        FROM file_transfers
        WHERE id = ?
    """, (transfer_id,)).fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "contact_id": row[1],
        "direction": row[2],
        "filename": row[3],
        "size": row[4],
        "hash": row[5],
        "bytes_transferred": row[6],
        "state": row[7],
        "created_at": row[8],
        "updated_at": row[9]
    }


def get_pending_transfers(contact_id: int) -> list[dict]:
    """
    Get all incomplete transfers for a contact.

    Args:
        contact_id: Contact database ID

    Returns:
        List of transfer state dictionaries
    """
    conn = get_database()
    rows = conn.execute("""
        SELECT id, contact_id, direction, filename, size, hash,
               bytes_transferred, state, created_at, updated_at
        FROM file_transfers
        WHERE contact_id = ? AND state IN ('pending', 'active', 'paused')
        ORDER BY created_at DESC
    """, (contact_id,)).fetchall()

    return [
        {
            "id": row[0],
            "contact_id": row[1],
            "direction": row[2],
            "filename": row[3],
            "size": row[4],
            "hash": row[5],
            "bytes_transferred": row[6],
            "state": row[7],
            "created_at": row[8],
            "updated_at": row[9]
        }
        for row in rows
    ]


def update_transfer_progress(
    transfer_id: str,
    bytes_transferred: int,
    state: str
) -> bool:
    """
    Update transfer progress.

    Args:
        transfer_id: Transfer UUID
        bytes_transferred: Current bytes transferred
        state: Current state

    Returns:
        True if updated, False if transfer not found
    """
    import time
    conn = get_database()
    timestamp = int(time.time() * 1000)

    cursor = conn.execute("""
        UPDATE file_transfers
        SET bytes_transferred = ?, state = ?, updated_at = ?
        WHERE id = ?
    """, (bytes_transferred, state, timestamp, transfer_id))
    conn.commit()

    return cursor.rowcount > 0


def delete_transfer(transfer_id: str) -> bool:
    """
    Delete transfer record from database.

    Args:
        transfer_id: Transfer UUID

    Returns:
        True if deleted, False if not found
    """
    conn = get_database()
    cursor = conn.execute("DELETE FROM file_transfers WHERE id = ?", (transfer_id,))
    conn.commit()

    return cursor.rowcount > 0
