"""
Sender Keys protocol for group message encryption.

Each group member maintains their own Sender Key, which consists of:
- Chain Key: 32-byte symmetric key that advances with each message (forward secrecy)
- Signature Key: Ed25519 key pair for message authentication

Messages are encrypted once with AES-GCM and broadcast to all group members.
Recipients use the sender's Sender Key to decrypt.

Based on Signal Sender Keys specification, using existing cryptography primitives.
"""

import os
import hashlib
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey
)
from cryptography.exceptions import InvalidSignature


# Domain separation constants
CHAIN_ADVANCE_INFO = b"DiscordOpus_SenderKey_ChainAdvance_v1"
MESSAGE_KEY_INFO = b"DiscordOpus_SenderKey_MessageKey_v1"


@dataclass
class EncryptedGroupMessage:
    """Encrypted group message with signature."""
    ciphertext: bytes  # AES-GCM encrypted (nonce || ciphertext)
    signature: bytes   # Ed25519 signature of ciphertext
    message_index: int  # Chain position for key derivation

    def to_dict(self) -> dict:
        """Convert to JSON-serializable format."""
        return {
            "ciphertext": self.ciphertext.hex(),
            "signature": self.signature.hex(),
            "message_index": self.message_index
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EncryptedGroupMessage":
        """Create from dictionary."""
        return cls(
            ciphertext=bytes.fromhex(data["ciphertext"]),
            signature=bytes.fromhex(data["signature"]),
            message_index=data["message_index"]
        )


class SenderKey:
    """
    Sender Key for group message encryption.

    Each sender maintains their own key that ratchets forward.
    The chain key advances with each message for forward secrecy.

    Usage:
    1. Sender creates SenderKey and distributes public portion to group
    2. Sender encrypts messages with encrypt()
    3. Recipients use SenderKeyReceiver to decrypt with the distributed key

    Thread safety: NOT thread-safe. Use external locking if needed.
    """

    def __init__(
        self,
        chain_key: Optional[bytes] = None,
        signature_private: Optional[Ed25519PrivateKey] = None,
        message_index: int = 0
    ):
        """
        Initialize a Sender Key.

        Args:
            chain_key: Initial 32-byte chain key (random if not provided)
            signature_private: Ed25519 private key for signing (generated if not provided)
            message_index: Starting message index (default 0)
        """
        self.chain_key = chain_key or os.urandom(32)
        self.signature_private = signature_private or Ed25519PrivateKey.generate()
        self.message_index = message_index

    @property
    def signature_public(self) -> Ed25519PublicKey:
        """Get the public signing key."""
        return self.signature_private.public_key()

    @property
    def signature_public_bytes(self) -> bytes:
        """Get the public signing key as raw bytes."""
        return self.signature_public.public_bytes_raw()

    def _derive_message_key(self, chain_key: bytes) -> bytes:
        """
        Derive message encryption key from chain key using HKDF.

        Args:
            chain_key: Current chain key

        Returns:
            32-byte message key for AES-256-GCM
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=MESSAGE_KEY_INFO
        )
        return hkdf.derive(chain_key)

    def _advance_chain(self, chain_key: bytes) -> bytes:
        """
        Advance chain key using one-way hash.

        This provides forward secrecy - old chain keys cannot be derived
        from new ones.

        Args:
            chain_key: Current chain key

        Returns:
            New chain key
        """
        return hashlib.sha256(chain_key + CHAIN_ADVANCE_INFO).digest()

    def encrypt(self, plaintext: bytes) -> EncryptedGroupMessage:
        """
        Encrypt a message for broadcast to the group.

        The chain key advances after encryption, providing forward secrecy.

        Args:
            plaintext: Message to encrypt

        Returns:
            EncryptedGroupMessage with ciphertext, signature, and message index
        """
        # Derive message key from current chain key
        message_key = self._derive_message_key(self.chain_key)

        # Encrypt with AES-256-GCM
        nonce = os.urandom(12)
        aesgcm = AESGCM(message_key)
        ciphertext = nonce + aesgcm.encrypt(nonce, plaintext, None)

        # Sign the ciphertext
        signature = self.signature_private.sign(ciphertext)

        # Record current index
        current_index = self.message_index

        # Advance chain for forward secrecy
        self.chain_key = self._advance_chain(self.chain_key)
        self.message_index += 1

        return EncryptedGroupMessage(
            ciphertext=ciphertext,
            signature=signature,
            message_index=current_index
        )

    def export_public(self) -> dict:
        """
        Export public portion for distribution to group members.

        This is sent (encrypted via pairwise Signal session) to each member.
        They use this to create a SenderKeyReceiver.

        Returns:
            Dictionary with chain_key, signature_public, and message_index
        """
        return {
            "chain_key": self.chain_key.hex(),
            "signature_public": self.signature_public_bytes.hex(),
            "message_index": self.message_index
        }

    def export_private(self) -> dict:
        """
        Export full state including private key for persistence.

        Used to save our own Sender Key state to storage.

        Returns:
            Dictionary with all key material
        """
        return {
            "chain_key": self.chain_key.hex(),
            "signature_private": self.signature_private.private_bytes_raw().hex(),
            "message_index": self.message_index
        }

    @classmethod
    def from_private_export(cls, data: dict) -> "SenderKey":
        """
        Restore SenderKey from private export.

        Args:
            data: Dictionary from export_private()

        Returns:
            Restored SenderKey
        """
        return cls(
            chain_key=bytes.fromhex(data["chain_key"]),
            signature_private=Ed25519PrivateKey.from_private_bytes(
                bytes.fromhex(data["signature_private"])
            ),
            message_index=data["message_index"]
        )


class SenderKeyReceiver:
    """
    Receiver side of Sender Keys protocol.

    Created from the public portion of another member's SenderKey.
    Used to decrypt messages from that sender.

    Maintains chain key state that advances in sync with sender.
    """

    def __init__(
        self,
        chain_key: bytes,
        signature_public: Ed25519PublicKey,
        message_index: int = 0
    ):
        """
        Initialize receiver from sender's public key data.

        Args:
            chain_key: Sender's chain key
            signature_public: Sender's Ed25519 public key for verification
            message_index: Expected next message index
        """
        self.chain_key = chain_key
        self.signature_public = signature_public
        self.message_index = message_index

        # Cache for out-of-order message keys
        # Maps message_index -> message_key
        # Limited size to prevent memory exhaustion from malicious senders
        self._skipped_keys: dict[int, bytes] = {}
        self._max_skip = 1000  # Max messages to skip ahead

    @classmethod
    def from_public_export(cls, data: dict) -> "SenderKeyReceiver":
        """
        Create receiver from sender's public export.

        Args:
            data: Dictionary from SenderKey.export_public()

        Returns:
            SenderKeyReceiver instance
        """
        return cls(
            chain_key=bytes.fromhex(data["chain_key"]),
            signature_public=Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(data["signature_public"])
            ),
            message_index=data["message_index"]
        )

    def _derive_message_key(self, chain_key: bytes) -> bytes:
        """Derive message key from chain key using HKDF."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=MESSAGE_KEY_INFO
        )
        return hkdf.derive(chain_key)

    def _advance_chain(self, chain_key: bytes) -> bytes:
        """Advance chain key using one-way hash."""
        return hashlib.sha256(chain_key + CHAIN_ADVANCE_INFO).digest()

    def _skip_to_index(self, target_index: int) -> bytes:
        """
        Skip chain forward to target index, caching intermediate keys.

        Args:
            target_index: Message index to skip to

        Returns:
            Message key for target index

        Raises:
            ValueError: If skip distance exceeds max_skip
        """
        skip_count = target_index - self.message_index

        if skip_count > self._max_skip:
            raise ValueError(
                f"Message index {target_index} too far ahead "
                f"(current: {self.message_index}, max skip: {self._max_skip})"
            )

        # Advance chain, caching each key
        chain_key = self.chain_key
        for i in range(self.message_index, target_index):
            message_key = self._derive_message_key(chain_key)
            self._skipped_keys[i] = message_key
            chain_key = self._advance_chain(chain_key)

        # Derive target key and advance
        target_key = self._derive_message_key(chain_key)
        self.chain_key = self._advance_chain(chain_key)
        self.message_index = target_index + 1

        # Clean up old skipped keys (keep only recent ones)
        old_indices = [i for i in self._skipped_keys if i < self.message_index - 100]
        for i in old_indices:
            del self._skipped_keys[i]

        return target_key

    def decrypt(self, message: EncryptedGroupMessage) -> bytes:
        """
        Decrypt a message from the sender.

        Handles out-of-order messages by caching skipped keys.
        Verifies signature before decryption.

        Args:
            message: EncryptedGroupMessage to decrypt

        Returns:
            Decrypted plaintext

        Raises:
            InvalidSignature: If signature verification fails
            ValueError: If message index is invalid
            cryptography.exceptions: If decryption fails
        """
        # Verify signature first (fail fast if tampered)
        self.signature_public.verify(message.signature, message.ciphertext)

        # Get message key
        if message.message_index < self.message_index:
            # Out of order message - check cache
            if message.message_index in self._skipped_keys:
                message_key = self._skipped_keys.pop(message.message_index)
            else:
                raise ValueError(
                    f"Message index {message.message_index} already processed "
                    f"(current: {self.message_index})"
                )
        elif message.message_index == self.message_index:
            # Expected next message
            message_key = self._derive_message_key(self.chain_key)
            self.chain_key = self._advance_chain(self.chain_key)
            self.message_index += 1
        else:
            # Future message - skip ahead
            message_key = self._skip_to_index(message.message_index)

        # Decrypt with AES-256-GCM
        nonce = message.ciphertext[:12]
        ciphertext = message.ciphertext[12:]
        aesgcm = AESGCM(message_key)

        return aesgcm.decrypt(nonce, ciphertext, None)

    def export_state(self) -> dict:
        """
        Export state for persistence.

        Returns:
            Dictionary with chain_key, signature_public, message_index
        """
        return {
            "chain_key": self.chain_key.hex(),
            "signature_public": self.signature_public.public_bytes_raw().hex(),
            "message_index": self.message_index
        }

    @classmethod
    def from_state(cls, data: dict) -> "SenderKeyReceiver":
        """
        Restore from exported state.

        Args:
            data: Dictionary from export_state()

        Returns:
            Restored SenderKeyReceiver
        """
        return cls(
            chain_key=bytes.fromhex(data["chain_key"]),
            signature_public=Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(data["signature_public"])
            ),
            message_index=data["message_index"]
        )
