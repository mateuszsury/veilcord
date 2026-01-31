"""
Group messaging service with Sender Keys encryption.

Architecture:
1. Each member has their own SenderKey per group
2. SenderKey is distributed to members via pairwise Signal sessions
3. Messages are encrypted once with SenderKey and broadcast
4. Recipients decrypt using stored sender key state

Message flow:
- Send: encrypt_group_message() -> returns encrypted message for broadcast
- Receive: decrypt_group_message() -> returns plaintext

Key distribution:
- When joining: distribute_sender_key() sends our key to all members
- When receiving: handle_sender_key_distribution() stores received key
- When member leaves: rotate_sender_keys() regenerates our key
"""

import time
import asyncio
from typing import Optional, Callable, Dict
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from src.groups.models import SenderKeyState
from src.groups.sender_keys import SenderKey, SenderKeyReceiver, EncryptedGroupMessage
from src.storage import groups as group_storage


@dataclass
class GroupMessage:
    """A group message ready for network transmission."""
    group_id: str
    message_id: str
    sender_public_key: str
    timestamp: int
    encrypted: EncryptedGroupMessage

    def to_dict(self) -> dict:
        """Convert to JSON-serializable format for transmission."""
        return {
            "type": "group_message",
            "group_id": self.group_id,
            "message_id": self.message_id,
            "sender_public_key": self.sender_public_key,
            "timestamp": self.timestamp,
            "message_index": self.encrypted.message_index,
            "ciphertext": self.encrypted.ciphertext.hex(),
            "signature": self.encrypted.signature.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupMessage":
        """Parse from received network message."""
        return cls(
            group_id=data["group_id"],
            message_id=data["message_id"],
            sender_public_key=data["sender_public_key"],
            timestamp=data["timestamp"],
            encrypted=EncryptedGroupMessage(
                ciphertext=bytes.fromhex(data["ciphertext"]),
                signature=bytes.fromhex(data["signature"]),
                message_index=data["message_index"]
            )
        )


@dataclass
class SenderKeyDistribution:
    """Sender Key distribution message for pairwise sending."""
    group_id: str
    sender_public_key: str
    key_data: dict  # From SenderKey.export_public()

    def to_dict(self) -> dict:
        """Convert to JSON for encryption and transmission."""
        return {
            "type": "sender_key_distribution",
            "group_id": self.group_id,
            "sender_public_key": self.sender_public_key,
            "key_data": self.key_data
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SenderKeyDistribution":
        """Parse from received message."""
        return cls(
            group_id=data["group_id"],
            sender_public_key=data["sender_public_key"],
            key_data=data["key_data"]
        )


@dataclass
class GroupMessagingCallbacks:
    """Callbacks for group messaging events."""
    # Send encrypted pairwise message to contact
    # (contact_public_key: str, message: dict) -> None
    send_pairwise: Optional[Callable[[str, dict], None]] = None

    # Broadcast group message to all members
    # (group_id: str, message: dict) -> None
    broadcast_group_message: Optional[Callable[[str, dict], None]] = None

    # Notify of received group message
    # (group_id: str, sender_key: str, message_id: str, plaintext: str, timestamp: int) -> None
    on_group_message: Optional[Callable[[str, str, str, str, int], None]] = None

    # Notify of key rotation needed (member left)
    # (group_id: str) -> None
    on_key_rotation_needed: Optional[Callable[[str], None]] = None


class GroupMessagingService:
    """
    Service for encrypted group messaging using Sender Keys.

    Each group has:
    - Our own SenderKey (for sending)
    - SenderKeyReceivers for each other member (for receiving)

    Thread safety: Uses asyncio.Lock for key operations.
    """

    def __init__(self, local_public_key: str):
        """
        Initialize group messaging service.

        Args:
            local_public_key: Our Ed25519 public key (hex)
        """
        self.local_public_key = local_public_key
        self.callbacks = GroupMessagingCallbacks()

        # Our sender keys per group: group_id -> SenderKey
        self._our_keys: Dict[str, SenderKey] = {}

        # Receiver keys per group: group_id -> {sender_key -> SenderKeyReceiver}
        self._receiver_keys: Dict[str, Dict[str, SenderKeyReceiver]] = {}

        # Lock for key operations
        self._lock = asyncio.Lock()

    def set_callbacks(self, callbacks: GroupMessagingCallbacks) -> None:
        """Set messaging callbacks."""
        self.callbacks = callbacks

    # Sender Key Management

    async def get_or_create_sender_key(self, group_id: str) -> SenderKey:
        """
        Get or create our sender key for a group.

        Loads from storage if exists, creates new if not.

        Args:
            group_id: Group ID

        Returns:
            Our SenderKey for this group
        """
        async with self._lock:
            # Check memory cache
            if group_id in self._our_keys:
                return self._our_keys[group_id]

            # Check storage - look for our own key
            key_state = group_storage.get_sender_key(group_id, self.local_public_key)

            if key_state:
                # Reconstruct from storage
                # Note: We need to store private key too - this is handled separately
                # For now, create new key (private key not in sender_keys table)
                pass

            # Create new sender key
            sender_key = SenderKey()
            self._our_keys[group_id] = sender_key

            return sender_key

    async def distribute_sender_key(self, group_id: str) -> None:
        """
        Distribute our sender key to all group members.

        Called when:
        - We join a group
        - We rotate our key (member removed)

        Uses pairwise Signal sessions to encrypt the key to each member.
        """
        sender_key = await self.get_or_create_sender_key(group_id)
        members = group_storage.get_members(group_id)

        distribution = SenderKeyDistribution(
            group_id=group_id,
            sender_public_key=self.local_public_key,
            key_data=sender_key.export_public()
        )

        # Send to each member (except ourselves)
        for member in members:
            if member.public_key == self.local_public_key:
                continue

            if self.callbacks.send_pairwise:
                self.callbacks.send_pairwise(
                    member.public_key,
                    distribution.to_dict()
                )

    async def handle_sender_key_distribution(
        self,
        distribution: SenderKeyDistribution
    ) -> None:
        """
        Handle received sender key from another member.

        Creates or updates the SenderKeyReceiver for that member.

        Args:
            distribution: Received SenderKeyDistribution
        """
        async with self._lock:
            group_id = distribution.group_id
            sender_key = distribution.sender_public_key

            # Create receiver from key data
            receiver = SenderKeyReceiver.from_public_export(distribution.key_data)

            # Store in memory
            if group_id not in self._receiver_keys:
                self._receiver_keys[group_id] = {}
            self._receiver_keys[group_id][sender_key] = receiver

            # Persist to storage
            key_state = SenderKeyState(
                id=None,
                group_id=group_id,
                sender_public_key=sender_key,
                chain_key=bytes.fromhex(distribution.key_data["chain_key"]),
                signature_public=bytes.fromhex(distribution.key_data["signature_public"]),
                message_index=distribution.key_data["message_index"],
                updated_at=int(time.time() * 1000)
            )
            group_storage.save_sender_key(key_state)

    async def rotate_sender_key(self, group_id: str) -> None:
        """
        Rotate our sender key for a group.

        Called when a member is removed (they might have old key).
        Generates new key and distributes to remaining members.

        Args:
            group_id: Group to rotate key for
        """
        async with self._lock:
            # Generate new key
            new_key = SenderKey()
            self._our_keys[group_id] = new_key

        # Distribute new key
        await self.distribute_sender_key(group_id)

    # Message Encryption/Decryption

    async def encrypt_group_message(
        self,
        group_id: str,
        message_id: str,
        plaintext: str
    ) -> GroupMessage:
        """
        Encrypt a message for the group.

        Args:
            group_id: Group ID
            message_id: Unique message ID (UUID)
            plaintext: Message text to encrypt

        Returns:
            GroupMessage ready for broadcast

        Raises:
            ValueError: If group not found
        """
        sender_key = await self.get_or_create_sender_key(group_id)

        # Encrypt
        encrypted = sender_key.encrypt(plaintext.encode('utf-8'))

        return GroupMessage(
            group_id=group_id,
            message_id=message_id,
            sender_public_key=self.local_public_key,
            timestamp=int(time.time() * 1000),
            encrypted=encrypted
        )

    async def send_group_message(
        self,
        group_id: str,
        message_id: str,
        plaintext: str
    ) -> GroupMessage:
        """
        Encrypt and broadcast a message to the group.

        Args:
            group_id: Group ID
            message_id: Unique message ID
            plaintext: Message text

        Returns:
            Sent GroupMessage
        """
        message = await self.encrypt_group_message(group_id, message_id, plaintext)

        if self.callbacks.broadcast_group_message:
            self.callbacks.broadcast_group_message(group_id, message.to_dict())

        return message

    async def decrypt_group_message(self, message: GroupMessage) -> str:
        """
        Decrypt a received group message.

        Args:
            message: Received GroupMessage

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If sender key not found
            InvalidSignature: If signature verification fails
        """
        group_id = message.group_id
        sender_key = message.sender_public_key

        # Get receiver key
        async with self._lock:
            if group_id not in self._receiver_keys:
                self._receiver_keys[group_id] = {}

            if sender_key not in self._receiver_keys[group_id]:
                # Try to load from storage
                key_state = group_storage.get_sender_key(group_id, sender_key)
                if not key_state:
                    raise ValueError(
                        f"No sender key for {sender_key[:16]}... in group {group_id[:8]}..."
                    )

                # Reconstruct receiver
                receiver = SenderKeyReceiver(
                    chain_key=key_state.chain_key,
                    signature_public=Ed25519PublicKey.from_public_bytes(
                        key_state.signature_public
                    ),
                    message_index=key_state.message_index
                )
                self._receiver_keys[group_id][sender_key] = receiver

            receiver = self._receiver_keys[group_id][sender_key]

        # Decrypt
        plaintext_bytes = receiver.decrypt(message.encrypted)

        # Update storage with new state
        async with self._lock:
            state = receiver.export_state()
            key_state = SenderKeyState(
                id=None,
                group_id=group_id,
                sender_public_key=sender_key,
                chain_key=bytes.fromhex(state["chain_key"]),
                signature_public=bytes.fromhex(state["signature_public"]),
                message_index=state["message_index"],
                updated_at=int(time.time() * 1000)
            )
            group_storage.save_sender_key(key_state)

        return plaintext_bytes.decode('utf-8')

    async def handle_group_message(self, data: dict) -> Optional[str]:
        """
        Handle incoming group message from network.

        Args:
            data: Received message dictionary

        Returns:
            Decrypted plaintext if successful, None if failed
        """
        try:
            message = GroupMessage.from_dict(data)
            plaintext = await self.decrypt_group_message(message)

            if self.callbacks.on_group_message:
                self.callbacks.on_group_message(
                    message.group_id,
                    message.sender_public_key,
                    message.message_id,
                    plaintext,
                    message.timestamp
                )

            return plaintext

        except Exception as e:
            # Log error but don't crash
            print(f"Failed to decrypt group message: {e}")
            return None

    # Member change handling

    async def handle_member_removed(self, group_id: str, removed_key: str) -> None:
        """
        Handle a member being removed from the group.

        Triggers key rotation for forward secrecy.

        Args:
            group_id: Group ID
            removed_key: Removed member's public key
        """
        # Remove their receiver key
        async with self._lock:
            if group_id in self._receiver_keys:
                self._receiver_keys[group_id].pop(removed_key, None)

        # Delete from storage
        group_storage.delete_sender_key(group_id, removed_key)

        # Rotate our key (removed member had it)
        await self.rotate_sender_key(group_id)

        # Notify if needed
        if self.callbacks.on_key_rotation_needed:
            self.callbacks.on_key_rotation_needed(group_id)

    async def handle_member_joined(
        self,
        group_id: str,
        new_member_key: str
    ) -> None:
        """
        Handle a new member joining the group.

        Sends our current sender key to the new member.

        Args:
            group_id: Group ID
            new_member_key: New member's public key
        """
        sender_key = await self.get_or_create_sender_key(group_id)

        distribution = SenderKeyDistribution(
            group_id=group_id,
            sender_public_key=self.local_public_key,
            key_data=sender_key.export_public()
        )

        if self.callbacks.send_pairwise:
            self.callbacks.send_pairwise(new_member_key, distribution.to_dict())

    # Cleanup

    async def leave_group(self, group_id: str) -> None:
        """
        Clean up state when leaving a group.

        Args:
            group_id: Group ID
        """
        async with self._lock:
            self._our_keys.pop(group_id, None)
            self._receiver_keys.pop(group_id, None)

        # Storage cleanup is handled by GroupService
