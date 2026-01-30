"""
P2P messaging service integrating peer connections, encryption, and storage.

Manages the full P2P messaging lifecycle:
- WebRTC connection establishment via signaling
- Signal Protocol encryption/decryption
- Message delivery over data channels
- Message persistence in SQLCipher database
- Frontend notifications for UI updates

Usage:
    service = MessagingService()
    service.on_message = lambda contact_id, msg: print(f"New message from {contact_id}")
    service.send_signaling = lambda msg: signaling_client.send(msg)

    # Start P2P connection
    await service.initiate_connection(contact_id)

    # Send encrypted message
    await service.send_text_message(contact_id, "Hello!")
"""

import asyncio
import base64
import json
import logging
import uuid
from typing import Callable, Optional, Dict, Any

from src.network.peer_connection import (
    PeerConnectionManager,
    PeerConnection,
    P2PConnectionState
)
from src.network.data_channel import MessageChannel, ChannelMessage, MessageType
from src.crypto.message_crypto import (
    encrypt_message,
    decrypt_message,
    OutgoingMessage
)
from src.storage.messages import (
    save_message,
    update_message,
    delete_message,
    add_reaction,
    remove_reaction,
    get_messages as storage_get_messages,
    Message
)
from src.storage.contacts import (
    get_contact,
    get_contact_by_pubkey,
    Contact
)


logger = logging.getLogger(__name__)


def _message_to_dict(msg: Message) -> Dict[str, Any]:
    """Convert Message dataclass to JSON-serializable dict."""
    return {
        "id": msg.id,
        "conversationId": msg.conversation_id,
        "senderId": msg.sender_id,
        "type": msg.type,
        "body": msg.body,
        "replyTo": msg.reply_to,
        "edited": msg.edited,
        "deleted": msg.deleted,
        "timestamp": msg.timestamp,
        "receivedAt": msg.received_at
    }


class MessagingService:
    """
    High-level P2P messaging service.

    Coordinates peer connections, encryption, storage, and frontend notifications.
    All methods that interact with network are async.

    Callbacks (set by NetworkService):
    - on_message: Called when an incoming message is received and stored
    - on_connection_state: Called when P2P connection state changes
    - send_signaling: Called to send signaling messages (offer/answer/ice)
    """

    def __init__(self):
        self._peer_manager = PeerConnectionManager()
        self._channels: Dict[int, MessageChannel] = {}  # contact_id -> channel

        # Callbacks (set by consumer)
        self.on_message: Optional[Callable[[int, Dict[str, Any]], None]] = None
        self.on_connection_state: Optional[Callable[[int, P2PConnectionState], None]] = None
        self.send_signaling: Optional[Callable[[dict], None]] = None

    # ========== P2P Connection Management ==========

    async def initiate_connection(self, contact_id: int) -> str:
        """
        Initiate a P2P connection to a contact.

        Creates WebRTC offer and sends it via signaling server.
        The contact should respond with an answer via handle_answer().

        Args:
            contact_id: Contact database ID

        Returns:
            Generated offer SDP (also sent via signaling)

        Raises:
            ValueError: If contact not found
        """
        contact = get_contact(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")

        # Create peer connection
        peer = await self._peer_manager.create_connection(
            contact_public_key=contact.ed25519_public_pem,
            on_state_change=lambda state: self._on_peer_state_change(contact_id, state),
            on_message=lambda msg: self._on_peer_message(contact_id, msg)
        )

        # Create offer and wait for ICE gathering
        offer_sdp = await peer.create_offer_and_wait()

        # Create message channel wrapper
        self._channels[contact_id] = MessageChannel(peer)
        self._setup_channel_handlers(contact_id)

        # Send offer via signaling
        if self.send_signaling:
            self.send_signaling({
                "type": "p2p_offer",
                "to": contact.ed25519_public_pem,  # Target public key
                "sdp": offer_sdp
            })

        logger.info(f"Initiated P2P connection to contact {contact_id}")
        return offer_sdp

    async def handle_offer(self, from_public_key: str, offer_sdp: str) -> Optional[str]:
        """
        Handle incoming P2P offer from a contact.

        Creates WebRTC answer and sends it back via signaling.

        Args:
            from_public_key: Sender's Ed25519 public key (PEM format)
            offer_sdp: SDP offer string

        Returns:
            Answer SDP (also sent via signaling), or None if contact not found
        """
        # Find contact by public key
        contact = self._find_contact_by_pem(from_public_key)
        if not contact:
            logger.warning(f"Received P2P offer from unknown public key")
            return None

        # Create peer connection
        peer = await self._peer_manager.create_connection(
            contact_public_key=from_public_key,
            on_state_change=lambda state: self._on_peer_state_change(contact.id, state),
            on_message=lambda msg: self._on_peer_message(contact.id, msg)
        )

        # Create answer
        answer_sdp = await peer.create_answer_and_wait(offer_sdp)

        # Create message channel wrapper
        self._channels[contact.id] = MessageChannel(peer)
        self._setup_channel_handlers(contact.id)

        # Send answer via signaling
        if self.send_signaling:
            self.send_signaling({
                "type": "p2p_answer",
                "to": from_public_key,
                "sdp": answer_sdp
            })

        logger.info(f"Accepted P2P connection from contact {contact.id}")
        return answer_sdp

    async def handle_answer(self, from_public_key: str, answer_sdp: str) -> bool:
        """
        Handle incoming P2P answer from a contact.

        Completes the WebRTC handshake for a previously sent offer.

        Args:
            from_public_key: Sender's Ed25519 public key (PEM format)
            answer_sdp: SDP answer string

        Returns:
            True if answer was applied, False if no pending connection
        """
        peer = self._peer_manager.get_connection(from_public_key)
        if not peer:
            logger.warning(f"Received P2P answer but no pending connection")
            return False

        await peer.set_remote_answer(answer_sdp)
        logger.info(f"Completed P2P handshake with {from_public_key[:50]}...")
        return True

    def get_connection_state(self, contact_id: int) -> P2PConnectionState:
        """
        Get current P2P connection state for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            P2PConnectionState (defaults to DISCONNECTED if no connection)
        """
        channel = self._channels.get(contact_id)
        if not channel:
            return P2PConnectionState.DISCONNECTED
        return channel._peer.state

    async def close_connection(self, contact_id: int) -> None:
        """Close P2P connection to a contact."""
        contact = get_contact(contact_id)
        if contact:
            await self._peer_manager.close_connection(contact.ed25519_public_pem)

        if contact_id in self._channels:
            del self._channels[contact_id]

    async def close_all(self) -> None:
        """Close all P2P connections."""
        await self._peer_manager.close_all()
        self._channels.clear()

    # ========== Message Sending ==========

    async def send_text_message(
        self,
        contact_id: int,
        body: str,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an encrypted text message to a contact.

        The message is encrypted with Signal Protocol, sent over the data channel,
        and stored in the local database.

        Args:
            contact_id: Contact database ID
            body: Message text
            reply_to: Optional ID of message being replied to

        Returns:
            Dict with message info (id, timestamp, etc.)

        Raises:
            RuntimeError: If no P2P connection to contact
            ValueError: If encryption fails
        """
        channel = self._channels.get(contact_id)
        if not channel or not channel.connected:
            raise RuntimeError(f"No P2P connection to contact {contact_id}")

        # Encrypt message
        encrypted = await encrypt_message(contact_id, body)

        # Generate message ID
        message_id = str(uuid.uuid4())

        # Convert to base64 for transmission
        header_json = json.dumps(encrypted.header)
        header_b64 = base64.b64encode(header_json.encode()).decode()
        ciphertext_b64 = base64.b64encode(bytes.fromhex(encrypted.ciphertext_hex)).decode()
        ephemeral_b64 = None
        if encrypted.ephemeral_key_hex:
            ephemeral_b64 = base64.b64encode(bytes.fromhex(encrypted.ephemeral_key_hex)).decode()

        # Send over data channel
        channel.send_text(
            message_id=message_id,
            header_b64=header_b64,
            ciphertext_b64=ciphertext_b64,
            ephemeral_key_b64=ephemeral_b64,
            reply_to=reply_to
        )

        # Store locally
        msg = save_message(
            conversation_id=contact_id,
            sender_id="self",
            body=body,
            msg_type="text",
            reply_to=reply_to,
            message_id=message_id
        )

        logger.debug(f"Sent message {message_id} to contact {contact_id}")
        return _message_to_dict(msg)

    async def edit_message(
        self,
        contact_id: int,
        message_id: str,
        new_body: str
    ) -> bool:
        """
        Edit a previously sent message.

        Args:
            contact_id: Contact database ID
            message_id: ID of message to edit
            new_body: New message text

        Returns:
            True if edit was sent and stored

        Raises:
            RuntimeError: If no P2P connection
        """
        channel = self._channels.get(contact_id)
        if not channel or not channel.connected:
            raise RuntimeError(f"No P2P connection to contact {contact_id}")

        # Encrypt new body
        encrypted = await encrypt_message(contact_id, new_body)

        edit_id = str(uuid.uuid4())
        header_json = json.dumps(encrypted.header)
        header_b64 = base64.b64encode(header_json.encode()).decode()
        ciphertext_b64 = base64.b64encode(bytes.fromhex(encrypted.ciphertext_hex)).decode()

        # Send edit
        channel.send_edit(
            message_id=edit_id,
            target_id=message_id,
            header_b64=header_b64,
            ciphertext_b64=ciphertext_b64
        )

        # Update local storage
        update_message(message_id, new_body)

        logger.debug(f"Edited message {message_id}")
        return True

    async def delete_message(
        self,
        contact_id: int,
        message_id: str
    ) -> bool:
        """
        Delete a message (soft delete).

        Args:
            contact_id: Contact database ID
            message_id: ID of message to delete

        Returns:
            True if delete was sent

        Raises:
            RuntimeError: If no P2P connection
        """
        channel = self._channels.get(contact_id)
        if not channel or not channel.connected:
            raise RuntimeError(f"No P2P connection to contact {contact_id}")

        delete_id = str(uuid.uuid4())
        channel.send_delete(delete_id, message_id)

        # Soft delete locally
        delete_message(message_id, hard_delete=False)

        logger.debug(f"Deleted message {message_id}")
        return True

    async def send_reaction(
        self,
        contact_id: int,
        message_id: str,
        emoji: str,
        action: str = "add"
    ) -> bool:
        """
        Send a reaction to a message.

        Args:
            contact_id: Contact database ID
            message_id: ID of message to react to
            emoji: Unicode emoji character
            action: "add" or "remove"

        Returns:
            True if reaction was sent
        """
        channel = self._channels.get(contact_id)
        if not channel or not channel.connected:
            raise RuntimeError(f"No P2P connection to contact {contact_id}")

        reaction_id = str(uuid.uuid4())
        channel.send_reaction(reaction_id, message_id, emoji, action)

        # Update local storage
        if action == "add":
            add_reaction(message_id, "self", emoji)
        else:
            remove_reaction(message_id, "self", emoji)

        return True

    def send_typing(self, contact_id: int, active: bool = True) -> None:
        """
        Send typing indicator.

        Args:
            contact_id: Contact database ID
            active: True if typing, False if stopped
        """
        channel = self._channels.get(contact_id)
        if channel and channel.connected:
            channel.send_typing(active)

    # ========== Message Retrieval ==========

    def get_messages(
        self,
        contact_id: int,
        limit: int = 50,
        before_timestamp: Optional[int] = None
    ) -> list[Dict[str, Any]]:
        """
        Get messages for a conversation.

        Args:
            contact_id: Contact database ID
            limit: Maximum messages to return
            before_timestamp: For pagination (get older messages)

        Returns:
            List of message dicts (most recent first)
        """
        messages = storage_get_messages(contact_id, limit, before_timestamp)
        return [_message_to_dict(m) for m in messages]

    # ========== Internal Handlers ==========

    def _setup_channel_handlers(self, contact_id: int) -> None:
        """Set up message handlers for a channel."""
        channel = self._channels.get(contact_id)
        if not channel:
            return

        channel.on_text_message = lambda msg: asyncio.create_task(
            self._handle_incoming_text(contact_id, msg)
        )
        channel.on_edit_message = lambda msg: asyncio.create_task(
            self._handle_incoming_edit(contact_id, msg)
        )
        channel.on_delete_message = lambda msg: self._handle_incoming_delete(contact_id, msg)
        channel.on_reaction = lambda msg: self._handle_incoming_reaction(contact_id, msg)
        channel.on_typing = lambda msg: self._handle_incoming_typing(contact_id, msg)

    async def _handle_incoming_text(self, contact_id: int, msg: ChannelMessage) -> None:
        """Handle incoming encrypted text message."""
        try:
            payload = msg.payload

            # Decode from base64
            header_json = base64.b64decode(payload.get("header", "")).decode()
            header = json.loads(header_json)
            ciphertext_hex = base64.b64decode(payload.get("ciphertext", "")).hex()

            ephemeral_key_hex = None
            if payload.get("ephemeral_key"):
                ephemeral_key_hex = base64.b64decode(payload["ephemeral_key"]).hex()

            # Decrypt
            plaintext = await decrypt_message(
                contact_id,
                header,
                ciphertext_hex,
                ephemeral_key_hex
            )

            # Get contact public key for sender_id
            contact = get_contact(contact_id)
            sender_id = contact.ed25519_public_pem if contact else "unknown"

            # Store message
            stored = save_message(
                conversation_id=contact_id,
                sender_id=sender_id,
                body=plaintext,
                msg_type="text",
                reply_to=payload.get("reply_to"),
                message_id=msg.id,
                timestamp=msg.timestamp
            )

            # Notify frontend
            if self.on_message:
                self.on_message(contact_id, _message_to_dict(stored))

            logger.debug(f"Received message {msg.id} from contact {contact_id}")

        except Exception as e:
            logger.error(f"Failed to handle incoming message: {e}")

    async def _handle_incoming_edit(self, contact_id: int, msg: ChannelMessage) -> None:
        """Handle incoming message edit."""
        try:
            payload = msg.payload
            target_id = payload.get("target_id")

            # Decode and decrypt
            header_json = base64.b64decode(payload.get("header", "")).decode()
            header = json.loads(header_json)
            ciphertext_hex = base64.b64decode(payload.get("ciphertext", "")).hex()

            new_body = await decrypt_message(contact_id, header, ciphertext_hex)

            # Update storage
            update_message(target_id, new_body)

            # Notify frontend
            if self.on_message:
                self.on_message(contact_id, {
                    "type": "edit",
                    "targetId": target_id,
                    "newBody": new_body,
                    "timestamp": msg.timestamp
                })

        except Exception as e:
            logger.error(f"Failed to handle incoming edit: {e}")

    def _handle_incoming_delete(self, contact_id: int, msg: ChannelMessage) -> None:
        """Handle incoming message delete."""
        target_id = msg.payload.get("target_id")

        # Soft delete
        delete_message(target_id, hard_delete=False)

        # Notify frontend
        if self.on_message:
            self.on_message(contact_id, {
                "type": "delete",
                "targetId": target_id,
                "timestamp": msg.timestamp
            })

    def _handle_incoming_reaction(self, contact_id: int, msg: ChannelMessage) -> None:
        """Handle incoming reaction."""
        payload = msg.payload
        target_id = payload.get("target_id")
        emoji = payload.get("emoji")
        action = payload.get("action", "add")

        contact = get_contact(contact_id)
        sender_id = contact.ed25519_public_pem if contact else "unknown"

        if action == "add":
            add_reaction(target_id, sender_id, emoji)
        else:
            remove_reaction(target_id, sender_id, emoji)

        # Notify frontend
        if self.on_message:
            self.on_message(contact_id, {
                "type": "reaction",
                "targetId": target_id,
                "emoji": emoji,
                "action": action,
                "senderId": sender_id
            })

    def _handle_incoming_typing(self, contact_id: int, msg: ChannelMessage) -> None:
        """Handle incoming typing indicator."""
        active = msg.payload.get("active", True)

        if self.on_message:
            self.on_message(contact_id, {
                "type": "typing",
                "active": active
            })

    def _on_peer_state_change(self, contact_id: int, state: P2PConnectionState) -> None:
        """Handle peer connection state change."""
        logger.debug(f"P2P state for contact {contact_id}: {state.value}")

        if self.on_connection_state:
            self.on_connection_state(contact_id, state)

    def _on_peer_message(self, contact_id: int, raw_message: str) -> None:
        """Handle raw message from peer (routed through MessageChannel)."""
        # Messages are handled by MessageChannel's handlers
        pass

    def _find_contact_by_pem(self, public_key_pem: str) -> Optional[Contact]:
        """Find contact by Ed25519 public key in PEM format."""
        # Extract hex from PEM for lookup
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            if isinstance(public_key, ed25519.Ed25519PublicKey):
                public_bytes = public_key.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                return get_contact_by_pubkey(public_bytes.hex())
        except Exception:
            pass

        return None
