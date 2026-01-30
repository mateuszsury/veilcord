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
            'addedAt': contact.added_at
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

    # ========== System Methods ==========

    def ping(self) -> str:
        """Test method to verify bridge is working."""
        return "pong"
