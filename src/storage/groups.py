"""Group storage operations."""
import time
from typing import Optional
from src.storage.db import get_database
from src.groups.models import Group, GroupMember, SenderKeyState


def create_group(group: Group) -> Group:
    """
    Insert a new group into the database.

    Args:
        group: Group object to insert

    Returns:
        The inserted Group
    """
    conn = get_database()
    conn.execute("""
        INSERT INTO groups (id, name, creator_public_key, created_at, updated_at, invite_code, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        group.id, group.name, group.creator_public_key,
        group.created_at, group.updated_at, group.invite_code,
        1 if group.is_active else 0
    ))
    conn.commit()
    return group


def get_group(group_id: str) -> Optional[Group]:
    """Get a group by ID."""
    conn = get_database()
    row = conn.execute(
        "SELECT id, name, creator_public_key, created_at, updated_at, invite_code, is_active FROM groups WHERE id = ?",
        (group_id,)
    ).fetchone()

    if not row:
        return None

    return Group(
        id=row[0],
        name=row[1],
        creator_public_key=row[2],
        created_at=row[3],
        updated_at=row[4],
        invite_code=row[5],
        is_active=bool(row[6])
    )


def get_all_groups() -> list[Group]:
    """Get all active groups."""
    conn = get_database()
    rows = conn.execute(
        "SELECT id, name, creator_public_key, created_at, updated_at, invite_code, is_active FROM groups WHERE is_active = 1 ORDER BY updated_at DESC"
    ).fetchall()

    return [
        Group(
            id=row[0], name=row[1], creator_public_key=row[2],
            created_at=row[3], updated_at=row[4], invite_code=row[5],
            is_active=bool(row[6])
        )
        for row in rows
    ]


def update_group(group: Group) -> bool:
    """Update a group. Returns True if updated."""
    conn = get_database()
    group.updated_at = int(time.time() * 1000)
    cursor = conn.execute("""
        UPDATE groups SET name = ?, invite_code = ?, is_active = ?, updated_at = ?
        WHERE id = ?
    """, (group.name, group.invite_code, 1 if group.is_active else 0, group.updated_at, group.id))
    conn.commit()
    return cursor.rowcount > 0


def delete_group(group_id: str) -> bool:
    """Soft delete a group (set is_active = 0)."""
    conn = get_database()
    cursor = conn.execute(
        "UPDATE groups SET is_active = 0, updated_at = ? WHERE id = ?",
        (int(time.time() * 1000), group_id)
    )
    conn.commit()
    return cursor.rowcount > 0


# Group member operations

def add_member(member: GroupMember) -> GroupMember:
    """Add a member to a group."""
    conn = get_database()
    cursor = conn.execute("""
        INSERT INTO group_members (group_id, public_key, display_name, joined_at, is_admin)
        VALUES (?, ?, ?, ?, ?)
    """, (
        member.group_id, member.public_key, member.display_name,
        member.joined_at, 1 if member.is_admin else 0
    ))
    conn.commit()
    member.id = cursor.lastrowid
    return member


def get_members(group_id: str) -> list[GroupMember]:
    """Get all members of a group."""
    conn = get_database()
    rows = conn.execute("""
        SELECT id, group_id, public_key, display_name, joined_at, is_admin
        FROM group_members WHERE group_id = ? ORDER BY joined_at
    """, (group_id,)).fetchall()

    return [
        GroupMember(
            id=row[0], group_id=row[1], public_key=row[2],
            display_name=row[3], joined_at=row[4], is_admin=bool(row[5])
        )
        for row in rows
    ]


def get_member(group_id: str, public_key: str) -> Optional[GroupMember]:
    """Get a specific member by group and public key."""
    conn = get_database()
    row = conn.execute("""
        SELECT id, group_id, public_key, display_name, joined_at, is_admin
        FROM group_members WHERE group_id = ? AND public_key = ?
    """, (group_id, public_key)).fetchone()

    if not row:
        return None

    return GroupMember(
        id=row[0], group_id=row[1], public_key=row[2],
        display_name=row[3], joined_at=row[4], is_admin=bool(row[5])
    )


def remove_member(group_id: str, public_key: str) -> bool:
    """Remove a member from a group."""
    conn = get_database()
    cursor = conn.execute(
        "DELETE FROM group_members WHERE group_id = ? AND public_key = ?",
        (group_id, public_key)
    )
    conn.commit()
    return cursor.rowcount > 0


# Sender key operations

def save_sender_key(key_state: SenderKeyState) -> SenderKeyState:
    """Save or update a sender key state."""
    conn = get_database()
    key_state.updated_at = int(time.time() * 1000)

    conn.execute("""
        INSERT INTO sender_keys (group_id, sender_public_key, chain_key, signature_public, message_index, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(group_id, sender_public_key) DO UPDATE SET
            chain_key = excluded.chain_key,
            signature_public = excluded.signature_public,
            message_index = excluded.message_index,
            updated_at = excluded.updated_at
    """, (
        key_state.group_id, key_state.sender_public_key,
        key_state.chain_key, key_state.signature_public,
        key_state.message_index, key_state.updated_at
    ))
    conn.commit()

    # Get the ID if it was inserted
    if key_state.id is None:
        row = conn.execute(
            "SELECT id FROM sender_keys WHERE group_id = ? AND sender_public_key = ?",
            (key_state.group_id, key_state.sender_public_key)
        ).fetchone()
        if row:
            key_state.id = row[0]

    return key_state


def get_sender_key(group_id: str, sender_public_key: str) -> Optional[SenderKeyState]:
    """Get sender key state for a group member."""
    conn = get_database()
    row = conn.execute("""
        SELECT id, group_id, sender_public_key, chain_key, signature_public, message_index, updated_at
        FROM sender_keys WHERE group_id = ? AND sender_public_key = ?
    """, (group_id, sender_public_key)).fetchone()

    if not row:
        return None

    return SenderKeyState(
        id=row[0], group_id=row[1], sender_public_key=row[2],
        chain_key=row[3], signature_public=row[4],
        message_index=row[5], updated_at=row[6]
    )


def get_all_sender_keys(group_id: str) -> list[SenderKeyState]:
    """Get all sender keys for a group."""
    conn = get_database()
    rows = conn.execute("""
        SELECT id, group_id, sender_public_key, chain_key, signature_public, message_index, updated_at
        FROM sender_keys WHERE group_id = ?
    """, (group_id,)).fetchall()

    return [
        SenderKeyState(
            id=row[0], group_id=row[1], sender_public_key=row[2],
            chain_key=row[3], signature_public=row[4],
            message_index=row[5], updated_at=row[6]
        )
        for row in rows
    ]


def delete_sender_keys(group_id: str) -> int:
    """Delete all sender keys for a group. Returns count deleted."""
    conn = get_database()
    cursor = conn.execute("DELETE FROM sender_keys WHERE group_id = ?", (group_id,))
    conn.commit()
    return cursor.rowcount


def delete_sender_key(group_id: str, sender_public_key: str) -> bool:
    """Delete a specific sender key."""
    conn = get_database()
    cursor = conn.execute(
        "DELETE FROM sender_keys WHERE group_id = ? AND sender_public_key = ?",
        (group_id, sender_public_key)
    )
    conn.commit()
    return cursor.rowcount > 0
