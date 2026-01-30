"""
Message storage operations for P2P text messaging.

Uses SQLCipher encrypted database for persistent storage.
Messages are stored decrypted (SQLCipher handles at-rest encryption).
"""

import uuid
import time
from dataclasses import dataclass
from typing import Optional

from src.storage.db import get_database


@dataclass
class Message:
    """Represents a chat message."""
    id: str
    conversation_id: int  # Contact ID
    sender_id: str  # 'self' for outgoing, public key for incoming
    type: str  # 'text', 'edit', 'delete', 'file'
    body: Optional[str]
    reply_to: Optional[str]
    edited: bool
    deleted: bool
    timestamp: int  # Unix ms
    received_at: Optional[int]
    file_id: Optional[int] = None  # Reference to files table


@dataclass
class Reaction:
    """Represents an emoji reaction to a message."""
    id: int
    message_id: str
    sender_id: str
    emoji: str
    timestamp: int


def save_message(
    conversation_id: int,
    sender_id: str,
    body: str,
    msg_type: str = "text",
    reply_to: Optional[str] = None,
    message_id: Optional[str] = None,
    timestamp: Optional[int] = None,
    file_id: Optional[int] = None
) -> Message:
    """
    Save a new message to the database.

    Args:
        conversation_id: Contact ID for the conversation
        sender_id: 'self' for outgoing, public key for incoming
        body: Message text content
        msg_type: Message type ('text', 'edit', 'delete', 'file')
        reply_to: ID of message being replied to
        message_id: Optional custom message ID (generated if not provided)
        timestamp: Optional custom timestamp (current time if not provided)
        file_id: Optional file ID for file messages

    Returns:
        Created Message object
    """
    conn = get_database()

    msg_id = message_id or str(uuid.uuid4())
    ts = timestamp or int(time.time() * 1000)
    received_at = int(time.time() * 1000) if sender_id != 'self' else None

    conn.execute("""
        INSERT INTO messages (id, conversation_id, sender_id, type, body, reply_to, timestamp, received_at, file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, conversation_id, sender_id, msg_type, body, reply_to, ts, received_at, file_id))
    conn.commit()

    return Message(
        id=msg_id,
        conversation_id=conversation_id,
        sender_id=sender_id,
        type=msg_type,
        body=body,
        reply_to=reply_to,
        edited=False,
        deleted=False,
        timestamp=ts,
        received_at=received_at,
        file_id=file_id
    )


def save_file_message(
    conversation_id: int,
    sender_id: str,
    file_id: int,
    filename: str,
    message_id: Optional[str] = None,
    timestamp: Optional[int] = None
) -> Message:
    """
    Save a file message to the database.

    Args:
        conversation_id: Contact ID for the conversation
        sender_id: 'self' for outgoing, public key for incoming
        file_id: ID from files table
        filename: Name of the file (used as message body)
        message_id: Optional custom message ID (generated if not provided)
        timestamp: Optional custom timestamp (current time if not provided)

    Returns:
        Created Message object
    """
    return save_message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        body=filename,
        msg_type="file",
        file_id=file_id,
        message_id=message_id,
        timestamp=timestamp
    )


def get_messages(
    conversation_id: int,
    limit: int = 50,
    before_timestamp: Optional[int] = None
) -> list[Message]:
    """
    Get messages for a conversation, ordered by timestamp descending.

    Args:
        conversation_id: Contact ID
        limit: Maximum number of messages to return
        before_timestamp: Only get messages before this timestamp (for pagination)

    Returns:
        List of Message objects (most recent first)
    """
    conn = get_database()

    if before_timestamp:
        rows = conn.execute("""
            SELECT id, conversation_id, sender_id, type, body, reply_to, edited, deleted, timestamp, received_at, file_id
            FROM messages
            WHERE conversation_id = ? AND timestamp < ? AND deleted = 0
            ORDER BY timestamp DESC
            LIMIT ?
        """, (conversation_id, before_timestamp, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT id, conversation_id, sender_id, type, body, reply_to, edited, deleted, timestamp, received_at, file_id
            FROM messages
            WHERE conversation_id = ? AND deleted = 0
            ORDER BY timestamp DESC
            LIMIT ?
        """, (conversation_id, limit)).fetchall()

    return [Message(
        id=row[0],
        conversation_id=row[1],
        sender_id=row[2],
        type=row[3],
        body=row[4],
        reply_to=row[5],
        edited=bool(row[6]),
        deleted=bool(row[7]),
        timestamp=row[8],
        received_at=row[9],
        file_id=row[10]
    ) for row in rows]


def get_message(message_id: str) -> Optional[Message]:
    """Get a single message by ID."""
    conn = get_database()
    row = conn.execute("""
        SELECT id, conversation_id, sender_id, type, body, reply_to, edited, deleted, timestamp, received_at, file_id
        FROM messages WHERE id = ?
    """, (message_id,)).fetchone()

    if not row:
        return None

    return Message(
        id=row[0],
        conversation_id=row[1],
        sender_id=row[2],
        type=row[3],
        body=row[4],
        reply_to=row[5],
        edited=bool(row[6]),
        deleted=bool(row[7]),
        timestamp=row[8],
        received_at=row[9],
        file_id=row[10]
    )


def update_message(message_id: str, new_body: str) -> bool:
    """
    Update message body (for edit).

    Args:
        message_id: ID of message to update
        new_body: New message text

    Returns:
        True if message was updated, False if not found
    """
    conn = get_database()
    cursor = conn.execute("""
        UPDATE messages SET body = ?, edited = 1 WHERE id = ?
    """, (new_body, message_id))
    conn.commit()
    return cursor.rowcount > 0


def delete_message(message_id: str, hard_delete: bool = False) -> bool:
    """
    Delete a message.

    Args:
        message_id: ID of message to delete
        hard_delete: If True, permanently remove; if False, soft delete (mark deleted)

    Returns:
        True if message was deleted, False if not found
    """
    conn = get_database()

    if hard_delete:
        cursor = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    else:
        cursor = conn.execute(
            "UPDATE messages SET deleted = 1, body = NULL WHERE id = ?",
            (message_id,)
        )

    conn.commit()
    return cursor.rowcount > 0


def add_reaction(message_id: str, sender_id: str, emoji: str) -> Optional[Reaction]:
    """
    Add an emoji reaction to a message.

    Args:
        message_id: ID of message to react to
        sender_id: 'self' or contact public key
        emoji: Unicode emoji character

    Returns:
        Created Reaction or None if duplicate
    """
    conn = get_database()
    ts = int(time.time() * 1000)

    try:
        cursor = conn.execute("""
            INSERT INTO reactions (message_id, sender_id, emoji, timestamp)
            VALUES (?, ?, ?, ?)
        """, (message_id, sender_id, emoji, ts))
        conn.commit()

        return Reaction(
            id=cursor.lastrowid,
            message_id=message_id,
            sender_id=sender_id,
            emoji=emoji,
            timestamp=ts
        )
    except Exception:
        # Duplicate reaction (UNIQUE constraint violated)
        return None


def remove_reaction(message_id: str, sender_id: str, emoji: str) -> bool:
    """
    Remove an emoji reaction from a message.

    Returns:
        True if reaction was removed, False if not found
    """
    conn = get_database()
    cursor = conn.execute("""
        DELETE FROM reactions WHERE message_id = ? AND sender_id = ? AND emoji = ?
    """, (message_id, sender_id, emoji))
    conn.commit()
    return cursor.rowcount > 0


def get_reactions(message_id: str) -> list[Reaction]:
    """Get all reactions for a message."""
    conn = get_database()
    rows = conn.execute("""
        SELECT id, message_id, sender_id, emoji, timestamp
        FROM reactions WHERE message_id = ?
        ORDER BY timestamp
    """, (message_id,)).fetchall()

    return [Reaction(
        id=row[0],
        message_id=row[1],
        sender_id=row[2],
        emoji=row[3],
        timestamp=row[4]
    ) for row in rows]


# Signal session state persistence

def save_signal_session(contact_id: int, session_state: bytes) -> None:
    """
    Save Signal Protocol session state for a contact.

    Called after every encrypt/decrypt to persist Double Ratchet state.

    Args:
        contact_id: Contact ID
        session_state: Serialized DoubleRatchet state bytes
    """
    conn = get_database()
    ts = int(time.time() * 1000)

    conn.execute("""
        INSERT OR REPLACE INTO signal_sessions (contact_id, session_state, updated_at)
        VALUES (?, ?, ?)
    """, (contact_id, session_state, ts))
    conn.commit()


def get_signal_session(contact_id: int) -> Optional[bytes]:
    """
    Get Signal Protocol session state for a contact.

    Returns:
        Serialized session state bytes, or None if no session exists
    """
    conn = get_database()
    row = conn.execute("""
        SELECT session_state FROM signal_sessions WHERE contact_id = ?
    """, (contact_id,)).fetchone()

    return row[0] if row else None


def delete_signal_session(contact_id: int) -> bool:
    """Delete Signal session for a contact (forces re-initialization)."""
    conn = get_database()
    cursor = conn.execute(
        "DELETE FROM signal_sessions WHERE contact_id = ?",
        (contact_id,)
    )
    conn.commit()
    return cursor.rowcount > 0
