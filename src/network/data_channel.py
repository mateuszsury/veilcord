"""
High-level message channel abstraction for P2P messaging.

Wraps PeerConnection to provide simple send/receive API with:
- JSON message encoding/decoding
- Message type routing
- Typing indicator throttling
- Delivery acknowledgments

Message protocol:
{
    "type": "text|edit|delete|reaction|typing|ack",
    "id": "uuid",
    "timestamp": 1234567890123,
    ... type-specific fields
}
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
from enum import Enum

from src.network.peer_connection import PeerConnection, P2PConnectionState


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages sent over data channel."""
    TEXT = "text"
    EDIT = "edit"
    DELETE = "delete"
    REACTION = "reaction"
    TYPING = "typing"
    ACK = "ack"


@dataclass
class ChannelMessage:
    """Parsed message from data channel."""
    type: MessageType
    id: str
    timestamp: int
    payload: Dict[str, Any]


class MessageChannel:
    """
    High-level message channel for P2P communication.

    Provides typed message sending and receiving with:
    - JSON serialization
    - Message type routing to handlers
    - Typing indicator throttling (max 1 per 3 seconds)
    - Automatic acknowledgments

    Usage:
        channel = MessageChannel(peer_connection)
        channel.on_text_message = lambda msg: print(msg.payload)
        channel.send_text("Hello!", message_id="uuid", header_b64="...", ciphertext_b64="...")
    """

    # Typing indicator throttle (seconds)
    TYPING_THROTTLE = 3.0

    def __init__(self, peer: PeerConnection):
        self._peer = peer
        self._last_typing_sent: float = 0

        # Message handlers (set by consumer)
        self.on_text_message: Optional[Callable[[ChannelMessage], None]] = None
        self.on_edit_message: Optional[Callable[[ChannelMessage], None]] = None
        self.on_delete_message: Optional[Callable[[ChannelMessage], None]] = None
        self.on_reaction: Optional[Callable[[ChannelMessage], None]] = None
        self.on_typing: Optional[Callable[[ChannelMessage], None]] = None
        self.on_ack: Optional[Callable[[ChannelMessage], None]] = None

        # Set up message routing
        self._peer.on_message = self._handle_message

    @property
    def connected(self) -> bool:
        """Check if channel is ready for messages."""
        return self._peer.state == P2PConnectionState.CONNECTED

    @property
    def contact_public_key(self) -> str:
        """Get the contact's public key for this channel."""
        return self._peer.contact_public_key

    def _handle_message(self, raw_message: str) -> None:
        """Route incoming message to appropriate handler."""
        try:
            data = json.loads(raw_message)
            msg_type = MessageType(data.get("type", "text"))
            msg = ChannelMessage(
                type=msg_type,
                id=data.get("id", ""),
                timestamp=data.get("timestamp", 0),
                payload=data
            )

            # Route to handler
            handlers = {
                MessageType.TEXT: self.on_text_message,
                MessageType.EDIT: self.on_edit_message,
                MessageType.DELETE: self.on_delete_message,
                MessageType.REACTION: self.on_reaction,
                MessageType.TYPING: self.on_typing,
                MessageType.ACK: self.on_ack,
            }

            handler = handlers.get(msg_type)
            if handler:
                handler(msg)
            else:
                logger.debug(f"No handler for message type: {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {raw_message[:100]}")
        except ValueError as e:
            logger.error(f"Invalid message type: {e}")

    def _send(self, msg_type: MessageType, data: Dict[str, Any]) -> None:
        """Send a message over the data channel."""
        message = {
            "type": msg_type.value,
            "timestamp": int(time.time() * 1000),
            **data
        }
        self._peer.send(json.dumps(message))

    def send_text(
        self,
        message_id: str,
        header_b64: str,
        ciphertext_b64: str,
        ephemeral_key_b64: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> None:
        """
        Send an encrypted text message.

        Args:
            message_id: UUID for this message
            header_b64: Base64-encoded Double Ratchet header
            ciphertext_b64: Base64-encoded encrypted message body
            ephemeral_key_b64: Base64-encoded ephemeral key (first message only)
            reply_to: ID of message being replied to
        """
        data: Dict[str, Any] = {
            "id": message_id,
            "header": header_b64,
            "ciphertext": ciphertext_b64,
        }
        if ephemeral_key_b64:
            data["ephemeral_key"] = ephemeral_key_b64
        if reply_to:
            data["reply_to"] = reply_to

        self._send(MessageType.TEXT, data)

    def send_edit(
        self,
        message_id: str,
        target_id: str,
        header_b64: str,
        ciphertext_b64: str
    ) -> None:
        """
        Send a message edit.

        Args:
            message_id: New UUID for this edit
            target_id: ID of the message being edited
            header_b64: Encrypted new content header
            ciphertext_b64: Encrypted new content
        """
        self._send(MessageType.EDIT, {
            "id": message_id,
            "target_id": target_id,
            "header": header_b64,
            "ciphertext": ciphertext_b64,
        })

    def send_delete(self, message_id: str, target_id: str) -> None:
        """
        Send a message deletion.

        Args:
            message_id: UUID for this delete message
            target_id: ID of message being deleted
        """
        self._send(MessageType.DELETE, {
            "id": message_id,
            "target_id": target_id,
        })

    def send_reaction(
        self,
        message_id: str,
        target_id: str,
        emoji: str,
        action: str = "add"
    ) -> None:
        """
        Send a reaction to a message.

        Args:
            message_id: UUID for this reaction
            target_id: ID of message being reacted to
            emoji: Unicode emoji character
            action: "add" or "remove"
        """
        self._send(MessageType.REACTION, {
            "id": message_id,
            "target_id": target_id,
            "emoji": emoji,
            "action": action,
        })

    def send_typing(self, active: bool = True) -> None:
        """
        Send typing indicator.

        Throttled to max once per TYPING_THROTTLE seconds.

        Args:
            active: True if typing, False if stopped
        """
        now = time.time()
        if active and (now - self._last_typing_sent) < self.TYPING_THROTTLE:
            return  # Throttle

        self._last_typing_sent = now
        self._send(MessageType.TYPING, {"active": active})

    def send_ack(self, message_id: str) -> None:
        """
        Send delivery acknowledgment for a message.

        Args:
            message_id: ID of message being acknowledged
        """
        self._send(MessageType.ACK, {
            "id": message_id,
            "message_id": message_id,
        })
