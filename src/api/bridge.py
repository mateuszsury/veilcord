"""
PyWebView API bridge - exposes Python methods to JavaScript.

All methods in this class are available as window.pywebview.api.method_name()
in the React frontend.

IMPORTANT: All methods should return JSON-serializable values (dict, list, str, int, bool, None).
Complex objects should be converted to dicts.
"""

from typing import Optional, List, Dict, Any

from src.storage.identity_store import (
    get_or_create_identity,
    load_identity,
    update_display_name,
    save_identity
)
from src.storage.contacts import (
    get_contacts as _get_contacts,
    add_contact as _add_contact,
    remove_contact as _remove_contact,
    set_contact_verified as _set_contact_verified,
    Contact
)
from src.crypto.backup import (
    export_backup,
    import_backup,
    BackupError
)
from src.crypto.identity import Identity
from src.crypto.fingerprint import format_fingerprint
from src.network.service import get_network_service


class API:
    """
    PyWebView API class exposed to JavaScript.

    Usage in JavaScript:
        await window.pywebview.api.get_identity()
    """

    def _identity_to_dict(self, identity: Optional[Identity]) -> Optional[Dict[str, Any]]:
        """Convert Identity to JSON-serializable dict."""
        if identity is None:
            return None

        return {
            'publicKey': identity.shareable_id,
            'fingerprint': identity.fingerprint,
            'fingerprintFormatted': format_fingerprint(identity.fingerprint),
            'displayName': identity.display_name
        }

    def _contact_to_dict(self, contact: Contact) -> Dict[str, Any]:
        """Convert Contact to JSON-serializable dict."""
        return {
            'id': contact.id,
            'publicKey': contact.ed25519_public_pem,  # For display - could extract hex
            'fingerprint': contact.fingerprint,
            'fingerprintFormatted': format_fingerprint(contact.fingerprint),
            'displayName': contact.display_name,
            'verified': contact.verified,
            'addedAt': contact.added_at,
            'onlineStatus': contact.online_status
        }

    # ========== Identity Methods ==========

    def get_identity(self) -> Optional[Dict[str, Any]]:
        """Get current identity or None if not created."""
        identity = load_identity()
        return self._identity_to_dict(identity)

    def generate_identity(self, display_name: str = "Anonymous") -> Dict[str, Any]:
        """Generate new identity (creates if doesn't exist)."""
        identity = get_or_create_identity(display_name)
        return self._identity_to_dict(identity)

    def update_display_name(self, name: str) -> None:
        """Update identity display name."""
        update_display_name(name)

    # ========== Backup Methods ==========

    def export_backup(self, password: str) -> Dict[str, Any]:
        """
        Export identity as encrypted backup.

        Returns:
            Dict with 'backup' key containing JSON string
        """
        identity = load_identity()
        if identity is None:
            raise ValueError("No identity to backup")

        backup_json = export_backup(identity, password)
        return {'backup': backup_json}

    def import_backup(self, backup_json: str, password: str) -> Dict[str, Any]:
        """
        Import identity from encrypted backup.

        Returns:
            Imported identity dict
        """
        try:
            identity = import_backup(backup_json, password)
            save_identity(identity)
            return self._identity_to_dict(identity)
        except BackupError as e:
            raise ValueError(str(e)) from e

    # ========== Contact Methods ==========

    def get_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts."""
        contacts = _get_contacts()
        return [self._contact_to_dict(c) for c in contacts]

    def add_contact(self, public_key: str, display_name: str) -> Dict[str, Any]:
        """
        Add contact by public key.

        Args:
            public_key: Ed25519 public key as hex string (64 chars)
            display_name: Name to show for this contact
        """
        contact = _add_contact(public_key, display_name)
        return self._contact_to_dict(contact)

    def remove_contact(self, contact_id: int) -> None:
        """Remove contact by ID."""
        _remove_contact(contact_id)

    def set_contact_verified(self, contact_id: int, verified: bool) -> None:
        """Set contact verification status."""
        _set_contact_verified(contact_id, verified)

    # ========== Network Methods ==========

    def get_connection_state(self) -> str:
        """Get current signaling connection state."""
        try:
            service = get_network_service()
            return service.get_connection_state()
        except RuntimeError:
            return "disconnected"  # Service not started yet

    def get_signaling_server(self) -> str:
        """Get configured signaling server URL."""
        service = get_network_service()
        return service.get_signaling_server()

    def set_signaling_server(self, url: str) -> None:
        """Set signaling server URL (will reconnect)."""
        service = get_network_service()
        service.set_signaling_server(url)

    def get_user_status(self) -> str:
        """Get user's presence status."""
        service = get_network_service()
        return service.get_user_status()

    def set_user_status(self, status: str) -> None:
        """Set user's presence status (online/away/busy/invisible)."""
        valid_statuses = ["online", "away", "busy", "invisible"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        service = get_network_service()
        service.set_user_status(status)

    # ========== Messaging Methods ==========

    def initiate_p2p_connection(self, contact_id: int) -> None:
        """
        Initiate P2P connection to a contact.

        Sends WebRTC offer via signaling server.
        Connection state updates come via discordopus:p2p_state events.

        Args:
            contact_id: Contact database ID
        """
        service = get_network_service()
        service.initiate_p2p_connection(contact_id)

    def send_message(
        self,
        contact_id: int,
        body: str,
        reply_to: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send encrypted text message to a contact.

        The message is encrypted with Signal Protocol and sent over
        the P2P data channel. Also stored locally.

        Args:
            contact_id: Contact database ID
            body: Message text
            reply_to: Optional message ID being replied to

        Returns:
            Message dict with id, timestamp, etc. or None if failed
        """
        service = get_network_service()
        return service.send_text_message(contact_id, body, reply_to)

    def get_messages(
        self,
        contact_id: int,
        limit: int = 50,
        before: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation.

        Args:
            contact_id: Contact database ID
            limit: Maximum messages to return
            before: Timestamp for pagination (get older messages)

        Returns:
            List of message dicts (most recent first)
        """
        # Use MessagingService for this
        service = get_network_service()
        if service._messaging:
            return service._messaging.get_messages(contact_id, limit, before)
        return []

    def get_p2p_state(self, contact_id: int) -> str:
        """
        Get P2P connection state for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            State string: new, connecting, connected, disconnected, failed, closed
        """
        service = get_network_service()
        return service.get_p2p_connection_state(contact_id)

    def send_typing(self, contact_id: int, active: bool = True) -> None:
        """
        Send typing indicator to a contact.

        Throttled to max once per 3 seconds.

        Args:
            contact_id: Contact database ID
            active: True if typing, False if stopped
        """
        service = get_network_service()
        service.send_typing_indicator(contact_id, active)

    # ========== System Methods ==========

    def ping(self) -> str:
        """Test method to verify bridge is working."""
        return "pong"
