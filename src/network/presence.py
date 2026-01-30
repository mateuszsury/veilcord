"""
Presence state management for user status and contact online tracking.

The PresenceManager handles:
- User's own status (online, away, busy, invisible, offline)
- Contact presence updates from signaling server
- Status persistence across app restarts
"""

from enum import Enum
from typing import Callable

from src.storage.settings import get_setting, set_setting, Settings
from src.storage.contacts import (
    get_contacts,
    update_contact_online_status_by_pubkey,
)


class UserStatus(Enum):
    """User presence status values."""

    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    INVISIBLE = "invisible"
    OFFLINE = "offline"

    @property
    def value(self) -> str:
        """Return lowercase string representation."""
        return self._value_


class PresenceManager:
    """
    Manages user status and contact presence.

    Attributes:
        on_status_change: Callback invoked when a contact's status changes.
                         Called with (public_key: str, status: str).
    """

    def __init__(self, on_status_change: Callable[[str, str], None]) -> None:
        """
        Initialize presence manager.

        Args:
            on_status_change: Callback for contact status changes.
                            Called with (public_key_hex, new_status).
        """
        self._on_status_change = on_status_change

    def get_user_status(self) -> UserStatus:
        """
        Get user's current status from settings.

        Returns:
            UserStatus enum value, defaults to ONLINE if not set.
        """
        status_str = get_setting(Settings.USER_STATUS, "online")

        # Map string to enum
        try:
            return UserStatus(status_str)
        except ValueError:
            # Invalid status in database, reset to online
            return UserStatus.ONLINE

    def set_user_status(self, status: UserStatus) -> None:
        """
        Set and persist user's status.

        Args:
            status: New UserStatus to set.
        """
        set_setting(Settings.USER_STATUS, status.value)

    def update_contact_presence(self, public_key: str, status: str) -> None:
        """
        Update a contact's online status.

        Called when receiving presence updates from signaling server.
        Updates database and notifies UI via callback.

        Args:
            public_key: Contact's Ed25519 public key as hex string.
            status: New status string (online, away, busy, invisible, offline).
        """
        # Update in database
        update_contact_online_status_by_pubkey(public_key, status)

        # Notify UI
        self._on_status_change(public_key, status)

    def get_contacts_presence(self) -> dict[str, str]:
        """
        Get online status for all contacts.

        Returns:
            Dict mapping public key hex to status string.
        """
        contacts = get_contacts()
        result = {}

        for contact in contacts:
            # Extract public key from PEM and convert to hex
            # The PEM contains the full SubjectPublicKeyInfo, we need raw bytes
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import ed25519

                public_key = serialization.load_pem_public_key(
                    contact.ed25519_public_pem.encode('utf-8')
                )
                if isinstance(public_key, ed25519.Ed25519PublicKey):
                    public_key_hex = public_key.public_bytes_raw().hex()
                    result[public_key_hex] = contact.online_status
            except Exception:
                # Skip contacts with invalid keys
                pass

        return result

    def build_status_message(self) -> dict:
        """
        Build status update message for signaling server.

        Returns:
            JSON-serializable dict with type and status fields.
        """
        return {
            "type": "status_update",
            "status": self.get_user_status().value
        }
