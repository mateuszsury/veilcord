"""
Contact storage in SQLCipher database.
"""

from typing import List, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from src.storage.db import get_database
from src.crypto.fingerprint import generate_fingerprint


@dataclass
class Contact:
    """Contact data."""
    id: int
    ed25519_public_pem: str
    x25519_public_hex: str
    display_name: str
    fingerprint: str
    verified: bool
    added_at: str
    online_status: str = "unknown"


def get_contacts() -> List[Contact]:
    """Get all contacts."""
    db = get_database()
    rows = db.execute("""
        SELECT id, ed25519_public_pem, x25519_public_hex, display_name,
               fingerprint, verified, added_at, online_status
        FROM contacts
        ORDER BY display_name
    """).fetchall()

    return [
        Contact(
            id=row[0],
            ed25519_public_pem=row[1],
            x25519_public_hex=row[2],
            display_name=row[3],
            fingerprint=row[4],
            verified=bool(row[5]),
            added_at=row[6],
            online_status=row[7]
        )
        for row in rows
    ]


def get_contact(contact_id: int) -> Optional[Contact]:
    """Get contact by ID."""
    db = get_database()
    row = db.execute("""
        SELECT id, ed25519_public_pem, x25519_public_hex, display_name,
               fingerprint, verified, added_at, online_status
        FROM contacts WHERE id = ?
    """, (contact_id,)).fetchone()

    if row is None:
        return None

    return Contact(
        id=row[0],
        ed25519_public_pem=row[1],
        x25519_public_hex=row[2],
        display_name=row[3],
        fingerprint=row[4],
        verified=bool(row[5]),
        added_at=row[6],
        online_status=row[7]
    )


def add_contact(public_key_hex: str, display_name: str) -> Contact:
    """
    Add contact by Ed25519 public key.

    Args:
        public_key_hex: Ed25519 public key as hex string (64 chars)
        display_name: Display name for contact

    Returns:
        Created Contact object

    Raises:
        ValueError: If public key is invalid
    """
    # Parse and validate public key
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        if len(public_key_bytes) != 32:
            raise ValueError("Public key must be 32 bytes")

        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid public key: {e}") from e

    # Generate fingerprint
    fingerprint = generate_fingerprint(public_key)

    # Serialize to PEM for storage
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    # X25519 public key - we don't have it yet, use placeholder
    # Will be exchanged during connection in Phase 2
    x25519_hex = '0' * 64  # Placeholder

    db = get_database()
    cursor = db.execute("""
        INSERT INTO contacts (ed25519_public_pem, x25519_public_hex, display_name, fingerprint)
        VALUES (?, ?, ?, ?)
    """, (public_pem, x25519_hex, display_name, fingerprint))
    db.commit()

    return Contact(
        id=cursor.lastrowid,
        ed25519_public_pem=public_pem,
        x25519_public_hex=x25519_hex,
        display_name=display_name,
        fingerprint=fingerprint,
        verified=False,
        added_at="",  # SQLite default
        online_status="unknown"
    )


def remove_contact(contact_id: int) -> None:
    """Remove contact by ID."""
    db = get_database()
    db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    db.commit()


def set_contact_verified(contact_id: int, verified: bool) -> None:
    """Set contact verification status."""
    db = get_database()
    db.execute(
        "UPDATE contacts SET verified = ? WHERE id = ?",
        (1 if verified else 0, contact_id)
    )
    db.commit()


def update_contact_display_name(contact_id: int, name: str) -> None:
    """Update contact display name."""
    db = get_database()
    db.execute(
        "UPDATE contacts SET display_name = ? WHERE id = ?",
        (name, contact_id)
    )
    db.commit()


def update_contact_online_status(contact_id: int, status: str) -> None:
    """
    Update contact online status.

    Args:
        contact_id: Contact database ID
        status: One of: online, away, busy, invisible, offline, unknown
    """
    db = get_database()
    db.execute(
        "UPDATE contacts SET online_status = ? WHERE id = ?",
        (status, contact_id)
    )
    db.commit()


def update_contact_online_status_by_pubkey(public_key_hex: str, status: str) -> None:
    """
    Update contact online status by Ed25519 public key.

    Presence updates come by public key, not contact ID, so this function
    finds the contact by their public key and updates their status.

    Args:
        public_key_hex: Ed25519 public key as hex string (64 chars)
        status: One of: online, away, busy, invisible, offline, unknown
    """
    # Convert hex to PEM for lookup
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    except Exception:
        return  # Invalid key, silently ignore

    db = get_database()
    db.execute(
        "UPDATE contacts SET online_status = ? WHERE ed25519_public_pem = ?",
        (status, public_pem)
    )
    db.commit()


def get_contact_by_pubkey(public_key_hex: str) -> Optional[Contact]:
    """
    Find contact by Ed25519 public key.

    Args:
        public_key_hex: Ed25519 public key as hex string (64 chars)

    Returns:
        Contact if found, None otherwise
    """
    # Convert hex to PEM for lookup
    try:
        public_key_bytes = bytes.fromhex(public_key_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    except Exception:
        return None  # Invalid key

    db = get_database()
    row = db.execute("""
        SELECT id, ed25519_public_pem, x25519_public_hex, display_name,
               fingerprint, verified, added_at, online_status
        FROM contacts WHERE ed25519_public_pem = ?
    """, (public_pem,)).fetchone()

    if row is None:
        return None

    return Contact(
        id=row[0],
        ed25519_public_pem=row[1],
        x25519_public_hex=row[2],
        display_name=row[3],
        fingerprint=row[4],
        verified=bool(row[5]),
        added_at=row[6],
        online_status=row[7]
    )
