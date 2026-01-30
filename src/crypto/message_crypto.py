"""
High-level message encryption/decryption API.

Provides simple encrypt_message() and decrypt_message() functions that:
1. Load or create Signal session for the contact
2. Perform encryption/decryption
3. Persist updated session state

Usage:
    # Sending a message (first message)
    encrypted = await encrypt_message(contact_id, "Hello!")

    # Receiving a message
    plaintext = await decrypt_message(
        contact_id,
        header_dict,
        ciphertext_hex,
        ephemeral_key_hex  # Only for first message
    )

All encryption/decryption is async due to the underlying Signal library.
"""

import asyncio
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey

from src.crypto.signal_session import (
    SignalSession,
    EncryptedMessage,
    encrypted_message_to_dict,
    encrypted_message_from_dict,
    header_from_dict,
    Header
)
from src.storage.messages import (
    save_signal_session,
    get_signal_session,
    delete_signal_session
)
from src.storage.contacts import get_contact
from src.storage.identity_store import load_identity


@dataclass
class OutgoingMessage:
    """Encrypted message ready to send over data channel."""
    header: Dict[str, Any]  # Header as JSON-serializable dict
    ciphertext_hex: str  # Ciphertext as hex string
    ephemeral_key_hex: Optional[str]  # Ephemeral key hex (only for first message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for transmission."""
        return {
            "header": self.header,
            "ciphertext": self.ciphertext_hex,
            "ephemeral_key": self.ephemeral_key_hex
        }


def get_or_create_session(contact_id: int) -> tuple[SignalSession, bool]:
    """
    Get existing session or create new one for a contact.

    Args:
        contact_id: Contact database ID

    Returns:
        Tuple of (SignalSession, is_new_session)
    """
    # Try to load existing session
    session_data = get_signal_session(contact_id)
    if session_data:
        return SignalSession.deserialize(session_data), False

    # No existing session - will need to initialize
    return SignalSession(), True


async def encrypt_message(contact_id: int, plaintext: str) -> OutgoingMessage:
    """
    Encrypt a message for a contact.

    Handles session initialization if this is the first message.
    The first message to a contact will include an ephemeral key that
    the recipient needs for session establishment.

    Args:
        contact_id: Contact database ID
        plaintext: Message text to encrypt

    Returns:
        OutgoingMessage with encrypted data ready for transmission

    Raises:
        ValueError: If contact not found, missing X25519 key, or no identity
    """
    session, is_new = get_or_create_session(contact_id)
    ephemeral_key_hex: Optional[str] = None

    if is_new or not session.initialized:
        # Need to initialize session
        identity = load_identity()
        if not identity:
            raise ValueError("No identity found")

        contact = get_contact(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")

        # Get contact's X25519 public key
        their_x25519_hex = contact.x25519_public_hex
        if not their_x25519_hex or their_x25519_hex == '0' * 64:
            raise ValueError(
                "Contact missing X25519 public key. "
                "X25519 keys are exchanged during P2P connection."
            )

        their_x25519_public = X25519PublicKey.from_public_bytes(
            bytes.fromhex(their_x25519_hex)
        )

        # Initialize as sender with the first message
        ephemeral_key, encrypted = await session.initialize_as_sender(
            identity.x25519_private_key,
            their_x25519_public,
            plaintext.encode('utf-8')
        )

        ephemeral_key_hex = ephemeral_key.hex()
    else:
        # Session already initialized - just encrypt
        encrypted = await session.encrypt(plaintext.encode('utf-8'))

    # Persist session state
    save_signal_session(contact_id, session.serialize())

    # Convert to transmission format
    msg_dict = encrypted_message_to_dict(encrypted)

    return OutgoingMessage(
        header=msg_dict["header"],
        ciphertext_hex=msg_dict["ciphertext"],
        ephemeral_key_hex=ephemeral_key_hex
    )


async def decrypt_message(
    contact_id: int,
    header: Dict[str, Any],
    ciphertext_hex: str,
    ephemeral_key_hex: Optional[str] = None
) -> str:
    """
    Decrypt a message from a contact.

    Handles session initialization if this is the first message from them.

    Args:
        contact_id: Contact database ID
        header: Message header as dict (from transmission)
        ciphertext_hex: Ciphertext as hex string
        ephemeral_key_hex: Ephemeral key hex (required for first message)

    Returns:
        Decrypted message text

    Raises:
        ValueError: If decryption fails or session cannot be established
    """
    session, is_new = get_or_create_session(contact_id)

    if is_new or not session.initialized:
        # First message from this contact - need their ephemeral key
        if not ephemeral_key_hex:
            raise ValueError(
                "First message requires ephemeral key for session initialization"
            )

        identity = load_identity()
        if not identity:
            raise ValueError("No identity found")

        # Reconstruct encrypted message
        encrypted_msg = EncryptedMessage(
            header=header_from_dict(header),
            ciphertext=bytes.fromhex(ciphertext_hex)
        )

        # Initialize as receiver
        plaintext = await session.initialize_as_receiver(
            identity.x25519_private_key,
            bytes.fromhex(ephemeral_key_hex),
            encrypted_msg
        )
    else:
        # Session already initialized - just decrypt
        encrypted_msg = EncryptedMessage(
            header=header_from_dict(header),
            ciphertext=bytes.fromhex(ciphertext_hex)
        )
        plaintext = await session.decrypt(encrypted_msg)

    # Persist session state
    save_signal_session(contact_id, session.serialize())

    return plaintext.decode('utf-8')


def has_session(contact_id: int) -> bool:
    """Check if we have an existing session with a contact."""
    return get_signal_session(contact_id) is not None


def reset_session(contact_id: int) -> None:
    """
    Reset the session with a contact (force re-initialization).

    Use this if the session gets out of sync.
    """
    delete_signal_session(contact_id)


# Convenience functions for synchronous usage

def encrypt_message_sync(contact_id: int, plaintext: str) -> OutgoingMessage:
    """
    Synchronous wrapper for encrypt_message.

    Use this in non-async contexts (e.g., API bridge).
    """
    return asyncio.run(encrypt_message(contact_id, plaintext))


def decrypt_message_sync(
    contact_id: int,
    header: Dict[str, Any],
    ciphertext_hex: str,
    ephemeral_key_hex: Optional[str] = None
) -> str:
    """
    Synchronous wrapper for decrypt_message.

    Use this in non-async contexts (e.g., API bridge).
    """
    return asyncio.run(decrypt_message(
        contact_id, header, ciphertext_hex, ephemeral_key_hex
    ))
