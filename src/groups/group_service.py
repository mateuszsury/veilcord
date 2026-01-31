"""
Group lifecycle management service.

Coordinates group operations between storage, crypto, and network layers.
"""

import time
from typing import Optional, Callable
from dataclasses import dataclass

from src.groups.models import Group, GroupMember
from src.groups.invite import generate_invite_code, parse_invite_code, InviteData
from src.storage import groups as group_storage


@dataclass
class GroupServiceCallbacks:
    """Callbacks for group service events."""
    on_group_created: Optional[Callable[[Group], None]] = None
    on_group_joined: Optional[Callable[[Group], None]] = None
    on_group_left: Optional[Callable[[str], None]] = None  # group_id
    on_member_added: Optional[Callable[[str, GroupMember], None]] = None  # group_id, member
    on_member_removed: Optional[Callable[[str, str], None]] = None  # group_id, public_key


class GroupService:
    """
    Manages group lifecycle operations.

    Responsibilities:
    - Create and delete groups
    - Generate and validate invite codes
    - Add/remove members
    - Track membership state

    Does NOT handle:
    - Sender Keys distribution (see group_messaging.py)
    - Group call coordination (see call_mesh.py)
    - Network signaling (handled by NetworkService)
    """

    def __init__(self, local_public_key: str, local_display_name: str):
        """
        Initialize group service.

        Args:
            local_public_key: Our Ed25519 public key (hex or PEM)
            local_display_name: Our display name
        """
        self.local_public_key = local_public_key
        self.local_display_name = local_display_name
        self.callbacks = GroupServiceCallbacks()

    def set_callbacks(self, callbacks: GroupServiceCallbacks) -> None:
        """Set event callbacks."""
        self.callbacks = callbacks

    # Group creation

    def create_group(self, name: str) -> Group:
        """
        Create a new group.

        The creator is automatically added as admin member.

        Args:
            name: Group display name

        Returns:
            Created Group object
        """
        # Validate name
        name = name.strip()
        if not name:
            raise ValueError("Group name cannot be empty")
        if len(name) > 100:
            raise ValueError("Group name too long (max 100 characters)")

        # Create group
        group = Group.create(name=name, creator_public_key=self.local_public_key)
        group_storage.create_group(group)

        # Add creator as admin member
        creator_member = GroupMember.create(
            group_id=group.id,
            public_key=self.local_public_key,
            display_name=self.local_display_name,
            is_admin=True
        )
        group_storage.add_member(creator_member)

        # Notify
        if self.callbacks.on_group_created:
            self.callbacks.on_group_created(group)

        return group

    def get_group(self, group_id: str) -> Optional[Group]:
        """Get a group by ID."""
        return group_storage.get_group(group_id)

    def get_all_groups(self) -> list[Group]:
        """Get all active groups the user is in."""
        return group_storage.get_all_groups()

    def update_group_name(self, group_id: str, new_name: str) -> bool:
        """
        Update group name. Only creator can do this.

        Args:
            group_id: Group to update
            new_name: New display name

        Returns:
            True if updated, False if not found or not creator
        """
        group = group_storage.get_group(group_id)
        if not group:
            return False

        if group.creator_public_key != self.local_public_key:
            raise PermissionError("Only group creator can rename group")

        group.name = new_name.strip()
        return group_storage.update_group(group)

    # Invite management

    def generate_invite(self, group_id: str, expiry_days: int = 7) -> str:
        """
        Generate an invite code for a group.

        Only creator/admin can generate invites.

        Args:
            group_id: Group to invite to
            expiry_days: Days until invite expires

        Returns:
            Invite URL string
        """
        group = group_storage.get_group(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Check if user is admin
        member = group_storage.get_member(group_id, self.local_public_key)
        if not member or not member.is_admin:
            raise PermissionError("Only admins can generate invites")

        invite_code = generate_invite_code(
            group_id=group.id,
            group_name=group.name,
            creator_public_key=group.creator_public_key,
            expiry_seconds=expiry_days * 24 * 3600
        )

        # Store current invite code in group
        group.invite_code = invite_code
        group_storage.update_group(group)

        return invite_code

    def validate_invite(self, code: str) -> Optional[InviteData]:
        """
        Validate an invite code.

        Args:
            code: Invite URL or raw code

        Returns:
            InviteData if valid, None if invalid
        """
        try:
            return parse_invite_code(code)
        except ValueError:
            return None

    # Membership

    def join_group(self, invite_code: str) -> Group:
        """
        Join a group via invite code.

        Args:
            invite_code: Valid invite URL or code

        Returns:
            Joined Group object

        Raises:
            ValueError: If invite is invalid or expired
        """
        invite = parse_invite_code(invite_code)  # Raises on invalid

        # Check if group already exists locally
        existing = group_storage.get_group(invite.group_id)
        if existing:
            # Check if already a member
            member = group_storage.get_member(invite.group_id, self.local_public_key)
            if member:
                return existing  # Already joined

        # Create local group record if needed
        if not existing:
            group = Group(
                id=invite.group_id,
                name=invite.group_name,
                creator_public_key=invite.creator_public_key,
                created_at=int(time.time() * 1000),
                updated_at=int(time.time() * 1000),
                invite_code=invite_code,
                is_active=True
            )
            group_storage.create_group(group)
        else:
            group = existing

        # Add ourselves as member
        self_member = GroupMember.create(
            group_id=group.id,
            public_key=self.local_public_key,
            display_name=self.local_display_name,
            is_admin=False  # Only creator is admin
        )
        group_storage.add_member(self_member)

        # Notify
        if self.callbacks.on_group_joined:
            self.callbacks.on_group_joined(group)

        return group

    def leave_group(self, group_id: str) -> bool:
        """
        Leave a group.

        Args:
            group_id: Group to leave

        Returns:
            True if left, False if not found
        """
        group = group_storage.get_group(group_id)
        if not group:
            return False

        # Remove our membership
        group_storage.remove_member(group_id, self.local_public_key)

        # Mark group as inactive locally
        group.is_active = False
        group_storage.update_group(group)

        # Delete our sender keys for this group
        group_storage.delete_sender_keys(group_id)

        # Notify
        if self.callbacks.on_group_left:
            self.callbacks.on_group_left(group_id)

        return True

    def get_members(self, group_id: str) -> list[GroupMember]:
        """Get all members of a group."""
        return group_storage.get_members(group_id)

    def add_member(
        self,
        group_id: str,
        public_key: str,
        display_name: str
    ) -> GroupMember:
        """
        Add a member to a group (called when someone joins).

        This is typically called when we receive a "member joined"
        message from the network.

        Args:
            group_id: Group ID
            public_key: New member's public key
            display_name: New member's display name

        Returns:
            Created GroupMember
        """
        # Check if already exists
        existing = group_storage.get_member(group_id, public_key)
        if existing:
            return existing

        member = GroupMember.create(
            group_id=group_id,
            public_key=public_key,
            display_name=display_name,
            is_admin=False
        )
        group_storage.add_member(member)

        if self.callbacks.on_member_added:
            self.callbacks.on_member_added(group_id, member)

        return member

    def remove_member(self, group_id: str, public_key: str) -> bool:
        """
        Remove a member from a group.

        Only creator/admin can remove members.
        Creator cannot be removed.

        Args:
            group_id: Group ID
            public_key: Member's public key to remove

        Returns:
            True if removed

        Raises:
            PermissionError: If not admin or trying to remove creator
        """
        group = group_storage.get_group(group_id)
        if not group:
            return False

        # Check permissions
        self_member = group_storage.get_member(group_id, self.local_public_key)
        if not self_member or not self_member.is_admin:
            raise PermissionError("Only admins can remove members")

        # Cannot remove creator
        if public_key == group.creator_public_key:
            raise PermissionError("Cannot remove group creator")

        # Remove member
        removed = group_storage.remove_member(group_id, public_key)

        # Also delete their sender key
        group_storage.delete_sender_key(group_id, public_key)

        if removed and self.callbacks.on_member_removed:
            self.callbacks.on_member_removed(group_id, public_key)

        return removed

    def is_admin(self, group_id: str) -> bool:
        """Check if local user is admin of the group."""
        member = group_storage.get_member(group_id, self.local_public_key)
        return member is not None and member.is_admin

    def is_creator(self, group_id: str) -> bool:
        """Check if local user is creator of the group."""
        group = group_storage.get_group(group_id)
        return group is not None and group.creator_public_key == self.local_public_key

    def get_member_count(self, group_id: str) -> int:
        """Get number of members in a group."""
        return len(group_storage.get_members(group_id))
