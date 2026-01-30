"""
WebRTC peer connection manager using aiortc.

Manages RTCPeerConnection instances for P2P communication.
Handles ICE gathering, offer/answer exchange, and connection lifecycle.

CRITICAL: aiortc does NOT support trickle ICE. We must wait for
iceGatheringState == "complete" before sending offer/answer.

Usage:
    manager = PeerConnectionManager()
    pc = await manager.create_connection(contact_public_key)
    offer_sdp = await pc.create_offer_and_wait()  # Waits for ICE gathering
    # Send offer_sdp via signaling
    # Receive answer_sdp via signaling
    await pc.set_remote_answer(answer_sdp)
    # Connection established, data channel ready
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Dict

from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription, RTCIceServer
from aiortc.rtcdatachannel import RTCDataChannel

from src.network.stun import get_ice_servers


logger = logging.getLogger(__name__)


class P2PConnectionState(Enum):
    """State of P2P connection."""
    NEW = "new"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class PeerConnection:
    """
    Wrapper around aiortc RTCPeerConnection.

    Handles ICE gathering wait, offer/answer creation, and data channel setup.
    """
    contact_public_key: str
    pc: RTCPeerConnection
    data_channel: Optional[RTCDataChannel] = None
    state: P2PConnectionState = P2PConnectionState.NEW
    on_state_change: Optional[Callable[[P2PConnectionState], None]] = None
    on_message: Optional[Callable[[str], None]] = None
    _ice_gathering_complete: asyncio.Event = field(default_factory=asyncio.Event)

    async def create_offer_and_wait(self) -> str:
        """
        Create SDP offer and wait for ICE gathering to complete.

        CRITICAL: aiortc does not support trickle ICE. The returned SDP
        contains all ICE candidates because we wait for gathering to complete.

        Returns:
            Complete SDP offer string with all ICE candidates
        """
        # Create data channel BEFORE offer (required for SDP negotiation)
        self.data_channel = self.pc.createDataChannel(
            "messages",
            ordered=True  # Reliable, ordered delivery
        )
        self._setup_data_channel_handlers(self.data_channel)

        # Create offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        # Wait for ICE gathering to complete
        await self._wait_for_ice_gathering()

        # Return complete SDP with all candidates
        return self.pc.localDescription.sdp

    async def create_answer_and_wait(self, offer_sdp: str) -> str:
        """
        Accept offer and create SDP answer.

        Args:
            offer_sdp: Remote peer's SDP offer

        Returns:
            Complete SDP answer string with all ICE candidates
        """
        # Set remote offer
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await self.pc.setRemoteDescription(offer)

        # Create answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        # Wait for ICE gathering
        await self._wait_for_ice_gathering()

        return self.pc.localDescription.sdp

    async def set_remote_answer(self, answer_sdp: str) -> None:
        """
        Accept remote answer (call after create_offer_and_wait).

        Args:
            answer_sdp: Remote peer's SDP answer
        """
        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await self.pc.setRemoteDescription(answer)

    async def _wait_for_ice_gathering(self, timeout: float = 30.0) -> None:
        """
        Wait for ICE gathering to complete.

        Args:
            timeout: Maximum seconds to wait

        Raises:
            asyncio.TimeoutError: If gathering doesn't complete in time
        """
        if self.pc.iceGatheringState == "complete":
            return

        self._ice_gathering_complete.clear()
        try:
            await asyncio.wait_for(
                self._ice_gathering_complete.wait(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"ICE gathering timeout for {self.contact_public_key[:16]}")
            raise

    def _setup_data_channel_handlers(self, channel: RTCDataChannel) -> None:
        """Set up event handlers for data channel."""

        @channel.on("open")
        def on_open():
            logger.info(f"Data channel open with {self.contact_public_key[:16]}")
            self._set_state(P2PConnectionState.CONNECTED)

        @channel.on("close")
        def on_close():
            logger.info(f"Data channel closed with {self.contact_public_key[:16]}")
            self._set_state(P2PConnectionState.CLOSED)

        @channel.on("message")
        def on_message(message):
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            logger.debug(f"Message from {self.contact_public_key[:16]}: {message[:50]}...")
            if self.on_message:
                self.on_message(message)

    def _set_state(self, state: P2PConnectionState) -> None:
        """Update state and notify callback."""
        if self.state != state:
            self.state = state
            if self.on_state_change:
                self.on_state_change(state)

    def send(self, message: str) -> None:
        """
        Send message over data channel.

        Args:
            message: JSON string to send

        Raises:
            RuntimeError: If data channel not ready
        """
        if not self.data_channel or self.data_channel.readyState != "open":
            raise RuntimeError("Data channel not ready")
        self.data_channel.send(message)

    async def close(self) -> None:
        """Close the peer connection."""
        if self.data_channel:
            self.data_channel.close()
        await self.pc.close()
        self._set_state(P2PConnectionState.CLOSED)


class PeerConnectionManager:
    """
    Manages multiple peer connections.

    Creates and tracks RTCPeerConnection instances for each contact.
    Handles connection lifecycle and reconnection.
    """

    def __init__(self):
        self._connections: Dict[str, PeerConnection] = {}  # contact_key -> PeerConnection
        self._lock = asyncio.Lock()

    async def create_connection(
        self,
        contact_public_key: str,
        on_state_change: Optional[Callable[[P2PConnectionState], None]] = None,
        on_message: Optional[Callable[[str], None]] = None
    ) -> PeerConnection:
        """
        Create a new peer connection for a contact.

        Args:
            contact_public_key: Contact's Ed25519 public key
            on_state_change: Callback for connection state changes
            on_message: Callback for incoming messages

        Returns:
            PeerConnection wrapper ready for offer/answer exchange
        """
        async with self._lock:
            # Close existing connection if any
            if contact_public_key in self._connections:
                old_pc = self._connections[contact_public_key]
                await old_pc.close()

            # Create RTCPeerConnection with STUN servers
            ice_servers = get_ice_servers()
            config = RTCConfiguration(
                iceServers=[RTCIceServer(urls=s["urls"]) for s in ice_servers]
            )
            rtc_pc = RTCPeerConnection(configuration=config)

            # Create wrapper
            peer = PeerConnection(
                contact_public_key=contact_public_key,
                pc=rtc_pc,
                on_state_change=on_state_change,
                on_message=on_message
            )

            # Set up ICE gathering complete handler
            @rtc_pc.on("icegatheringstatechange")
            def on_ice_gathering_change():
                if rtc_pc.iceGatheringState == "complete":
                    peer._ice_gathering_complete.set()

            # Set up connection state handler
            @rtc_pc.on("connectionstatechange")
            async def on_connection_state_change():
                state_map = {
                    "new": P2PConnectionState.NEW,
                    "connecting": P2PConnectionState.CONNECTING,
                    "connected": P2PConnectionState.CONNECTED,
                    "disconnected": P2PConnectionState.DISCONNECTED,
                    "failed": P2PConnectionState.FAILED,
                    "closed": P2PConnectionState.CLOSED,
                }
                state = state_map.get(rtc_pc.connectionState, P2PConnectionState.NEW)
                peer._set_state(state)

                if state == P2PConnectionState.FAILED:
                    logger.warning(f"P2P connection failed with {contact_public_key[:16]}")
                    await peer.close()

            # Set up incoming data channel handler (for receiver side)
            @rtc_pc.on("datachannel")
            def on_datachannel(channel: RTCDataChannel):
                logger.info(f"Received data channel from {contact_public_key[:16]}")
                peer.data_channel = channel
                peer._setup_data_channel_handlers(channel)

            self._connections[contact_public_key] = peer
            return peer

    def get_connection(self, contact_public_key: str) -> Optional[PeerConnection]:
        """Get existing connection for a contact."""
        return self._connections.get(contact_public_key)

    async def close_connection(self, contact_public_key: str) -> None:
        """Close and remove connection for a contact."""
        async with self._lock:
            if contact_public_key in self._connections:
                await self._connections[contact_public_key].close()
                del self._connections[contact_public_key]

    async def close_all(self) -> None:
        """Close all connections."""
        async with self._lock:
            for peer in self._connections.values():
                await peer.close()
            self._connections.clear()
