"""
WebRTC mesh topology for group voice calls.

Mesh topology: Each participant maintains (N-1) peer connections.
For 4 participants: 3 connections per peer, 6 total edges in mesh.

Signaling coordination uses "polite/impolite peer" pattern:
- Higher public key = impolite = initiates connection
- Lower public key = polite = waits for offer

Bandwidth considerations:
- Audio: ~50 kbps per stream (Opus)
- Upload: (N-1) * 50 kbps
- Download: (N-1) * 50 kbps
- 4 participants = ~300 kbps total per peer

Practical limit: 4 participants for acceptable quality.
5+ participants should show warning and may degrade.
"""

import asyncio
from enum import Enum
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, field

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer

from src.voice.audio_track import MicrophoneAudioTrack


class GroupCallState(Enum):
    """State of the group call."""
    IDLE = "idle"
    JOINING = "joining"
    ACTIVE = "active"
    LEAVING = "leaving"
    ENDED = "ended"


@dataclass
class PeerConnectionState:
    """State of a single peer connection."""
    peer_key: str
    connection: RTCPeerConnection
    connected: bool = False
    audio_track_added: bool = False


@dataclass
class GroupCallCallbacks:
    """Callbacks for group call events."""
    # Send signaling message to specific peer
    # (peer_key: str, message: dict) -> None
    send_signaling: Optional[Callable[[str, dict], None]] = None

    # Broadcast signaling to all group members
    # (group_id: str, message: dict) -> None
    broadcast_signaling: Optional[Callable[[str, dict], None]] = None

    # State change notification
    # (state: GroupCallState, group_id: str) -> None
    on_state_change: Optional[Callable[[GroupCallState, str], None]] = None

    # Participant joined
    # (group_id: str, peer_key: str) -> None
    on_participant_joined: Optional[Callable[[str, str], None]] = None

    # Participant left
    # (group_id: str, peer_key: str) -> None
    on_participant_left: Optional[Callable[[str, str], None]] = None

    # Connection quality update
    # (group_id: str, peer_key: str, quality: str) -> None
    on_connection_quality: Optional[Callable[[str, str, str], None]] = None


@dataclass
class BandwidthEstimate:
    """Bandwidth estimation for group call."""
    upload_kbps: int
    download_kbps: int
    total_kbps: int
    participant_count: int
    warning: bool  # True if 5+ participants
    message: Optional[str] = None


# STUN configuration (same as 1:1 calls)
ICE_SERVERS = [
    RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
    RTCIceServer(urls=["stun:stun1.l.google.com:19302"]),
]

# Recommended participant limits
SOFT_LIMIT = 4  # Warning above this
HARD_LIMIT = 8  # Refuse above this

# Audio bitrate per stream (kbps)
AUDIO_BITRATE_KBPS = 50


class GroupCallMesh:
    """
    Manages WebRTC mesh topology for group voice calls.

    Each participant maintains (N-1) peer connections to all other participants.
    Audio is sent directly to each peer (no mixing, no SFU).

    Thread safety: Uses asyncio.Lock for state mutations.
    """

    def __init__(self, local_public_key: str, group_id: str):
        """
        Initialize group call mesh.

        Args:
            local_public_key: Our Ed25519 public key (hex)
            group_id: Group ID for this call
        """
        self.local_key = local_public_key
        self.group_id = group_id
        self.callbacks = GroupCallCallbacks()

        # State
        self._state = GroupCallState.IDLE
        self._call_id: Optional[str] = None

        # Peer connections: peer_key -> PeerConnectionState
        self._peers: Dict[str, PeerConnectionState] = {}

        # Our microphone track (shared across all connections)
        self._mic_track: Optional[MicrophoneAudioTrack] = None

        # Lock for state mutations
        self._lock = asyncio.Lock()

        # Track active participants
        self._participants: List[str] = []

    @property
    def state(self) -> GroupCallState:
        """Current call state."""
        return self._state

    @property
    def participant_count(self) -> int:
        """Number of participants including self."""
        return len(self._participants) + 1

    @property
    def connected_count(self) -> int:
        """Number of connected peers."""
        return sum(1 for p in self._peers.values() if p.connected)

    def set_callbacks(self, callbacks: GroupCallCallbacks) -> None:
        """Set event callbacks."""
        self.callbacks = callbacks

    def _set_state(self, new_state: GroupCallState) -> None:
        """Update state and notify."""
        if self._state != new_state:
            self._state = new_state
            if self.callbacks.on_state_change:
                self.callbacks.on_state_change(new_state, self.group_id)

    # Bandwidth estimation

    @staticmethod
    def estimate_bandwidth(participant_count: int) -> BandwidthEstimate:
        """
        Estimate bandwidth requirements for a group call.

        Args:
            participant_count: Total number of participants (including self)

        Returns:
            BandwidthEstimate with upload/download requirements
        """
        streams = participant_count - 1  # Send to N-1 peers

        upload = streams * AUDIO_BITRATE_KBPS
        download = streams * AUDIO_BITRATE_KBPS
        total = upload + download

        warning = participant_count > SOFT_LIMIT
        message = None

        if participant_count > HARD_LIMIT:
            message = f"Maximum {HARD_LIMIT} participants supported"
        elif warning:
            message = f"Audio quality may degrade with {participant_count} participants"

        return BandwidthEstimate(
            upload_kbps=upload,
            download_kbps=download,
            total_kbps=total,
            participant_count=participant_count,
            warning=warning,
            message=message
        )

    # Call lifecycle

    async def start_call(self, call_id: str, participants: List[str]) -> BandwidthEstimate:
        """
        Start a group call.

        Initiates connections to all participants.

        Args:
            call_id: Unique call identifier
            participants: List of participant public keys (including self)

        Returns:
            BandwidthEstimate for this call

        Raises:
            ValueError: If too many participants or invalid state
        """
        async with self._lock:
            if self._state != GroupCallState.IDLE:
                raise ValueError(f"Cannot start call in state {self._state}")

            if len(participants) > HARD_LIMIT:
                raise ValueError(f"Maximum {HARD_LIMIT} participants allowed")

            self._call_id = call_id
            self._participants = [p for p in participants if p != self.local_key]
            self._set_state(GroupCallState.JOINING)

        # Create microphone track
        self._mic_track = MicrophoneAudioTrack()

        # Broadcast call start
        if self.callbacks.broadcast_signaling:
            self.callbacks.broadcast_signaling(self.group_id, {
                "type": "group_call_start",
                "call_id": call_id,
                "from": self.local_key,
                "group_id": self.group_id,
                "participants": participants
            })

        # Initiate connections to peers
        # Use polite/impolite pattern: higher key initiates
        tasks = []
        for peer_key in self._participants:
            if self.local_key > peer_key:
                # We are impolite (higher key) - initiate
                tasks.append(self._initiate_connection(peer_key))
            # else: wait for them to initiate

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return self.estimate_bandwidth(len(participants))

    async def join_call(self, call_id: str, participants: List[str]) -> BandwidthEstimate:
        """
        Join an existing group call.

        Args:
            call_id: Call identifier
            participants: Current participants (including caller)

        Returns:
            BandwidthEstimate for this call
        """
        async with self._lock:
            if self._state != GroupCallState.IDLE:
                raise ValueError(f"Cannot join call in state {self._state}")

            self._call_id = call_id
            self._participants = [p for p in participants if p != self.local_key]
            self._set_state(GroupCallState.JOINING)

        # Create microphone track
        self._mic_track = MicrophoneAudioTrack()

        # Broadcast join
        if self.callbacks.broadcast_signaling:
            self.callbacks.broadcast_signaling(self.group_id, {
                "type": "group_call_join",
                "call_id": call_id,
                "from": self.local_key,
                "group_id": self.group_id
            })

        # Initiate connections where we are impolite
        tasks = []
        for peer_key in self._participants:
            if self.local_key > peer_key:
                tasks.append(self._initiate_connection(peer_key))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return self.estimate_bandwidth(len(participants) + 1)

    async def leave_call(self) -> None:
        """Leave the group call."""
        async with self._lock:
            if self._state in (GroupCallState.IDLE, GroupCallState.ENDED):
                return

            self._set_state(GroupCallState.LEAVING)

        # Broadcast leave
        if self.callbacks.broadcast_signaling:
            self.callbacks.broadcast_signaling(self.group_id, {
                "type": "group_call_leave",
                "call_id": self._call_id,
                "from": self.local_key,
                "group_id": self.group_id
            })

        # Close all connections
        await self._cleanup()

    # Connection management

    async def _initiate_connection(self, peer_key: str) -> None:
        """
        Initiate connection to a peer.

        Creates RTCPeerConnection, adds audio track, sends offer.

        Args:
            peer_key: Peer's public key
        """
        pc = await self._create_peer_connection(peer_key)

        # Add our audio track
        if self._mic_track:
            pc.addTrack(self._mic_track)

        # Create offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Wait for ICE gathering (aiortc doesn't support trickle ICE)
        await self._wait_for_ice_gathering(pc)

        # Send offer
        if self.callbacks.send_signaling:
            self.callbacks.send_signaling(peer_key, {
                "type": "group_call_offer",
                "call_id": self._call_id,
                "from": self.local_key,
                "group_id": self.group_id,
                "sdp": pc.localDescription.sdp,
                "sdp_type": pc.localDescription.type
            })

    async def _create_peer_connection(self, peer_key: str) -> RTCPeerConnection:
        """
        Create and configure a peer connection.

        Args:
            peer_key: Peer's public key

        Returns:
            Configured RTCPeerConnection
        """
        config = RTCConfiguration(iceServers=ICE_SERVERS)
        pc = RTCPeerConnection(config)

        # Store state
        state = PeerConnectionState(peer_key=peer_key, connection=pc)
        self._peers[peer_key] = state

        # Set up event handlers
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            await self._handle_connection_state_change(peer_key, pc.connectionState)

        @pc.on("track")
        def on_track(track):
            # Received audio track from peer
            if track.kind == "audio":
                # Track is automatically played by aiortc
                pass

        return pc

    async def _wait_for_ice_gathering(self, pc: RTCPeerConnection, timeout: float = 30.0) -> None:
        """Wait for ICE gathering to complete."""
        start = asyncio.get_event_loop().time()
        while pc.iceGatheringState != "complete":
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError("ICE gathering timed out")
            await asyncio.sleep(0.1)

    async def _handle_connection_state_change(self, peer_key: str, state: str) -> None:
        """Handle peer connection state change."""
        if peer_key not in self._peers:
            return

        peer_state = self._peers[peer_key]

        if state == "connected":
            peer_state.connected = True
            if self.callbacks.on_participant_joined:
                self.callbacks.on_participant_joined(self.group_id, peer_key)

            # Check if all peers connected
            if self.connected_count == len(self._participants):
                self._set_state(GroupCallState.ACTIVE)

        elif state in ("disconnected", "failed", "closed"):
            peer_state.connected = False
            if self.callbacks.on_participant_left:
                self.callbacks.on_participant_left(self.group_id, peer_key)

    # Signaling handlers

    async def handle_offer(self, peer_key: str, sdp: str, sdp_type: str) -> None:
        """
        Handle incoming WebRTC offer.

        Args:
            peer_key: Peer who sent the offer
            sdp: SDP offer
            sdp_type: SDP type (usually "offer")
        """
        pc = await self._create_peer_connection(peer_key)

        # Add our audio track
        if self._mic_track:
            pc.addTrack(self._mic_track)

        # Set remote description
        await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=sdp_type))

        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        # Wait for ICE
        await self._wait_for_ice_gathering(pc)

        # Send answer
        if self.callbacks.send_signaling:
            self.callbacks.send_signaling(peer_key, {
                "type": "group_call_answer",
                "call_id": self._call_id,
                "from": self.local_key,
                "group_id": self.group_id,
                "sdp": pc.localDescription.sdp,
                "sdp_type": pc.localDescription.type
            })

    async def handle_answer(self, peer_key: str, sdp: str, sdp_type: str) -> None:
        """
        Handle incoming WebRTC answer.

        Args:
            peer_key: Peer who sent the answer
            sdp: SDP answer
            sdp_type: SDP type (usually "answer")
        """
        if peer_key not in self._peers:
            return

        pc = self._peers[peer_key].connection
        await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=sdp_type))

    async def handle_participant_joined(self, peer_key: str) -> None:
        """
        Handle new participant joining the call.

        Args:
            peer_key: New participant's public key
        """
        async with self._lock:
            if peer_key in self._participants:
                return  # Already known
            self._participants.append(peer_key)

        # Initiate connection if we are impolite
        if self.local_key > peer_key:
            await self._initiate_connection(peer_key)

    async def handle_participant_left(self, peer_key: str) -> None:
        """
        Handle participant leaving the call.

        Args:
            peer_key: Leaving participant's public key
        """
        async with self._lock:
            if peer_key in self._participants:
                self._participants.remove(peer_key)

            if peer_key in self._peers:
                await self._peers[peer_key].connection.close()
                del self._peers[peer_key]

        if self.callbacks.on_participant_left:
            self.callbacks.on_participant_left(self.group_id, peer_key)

        # Check if call ended (no more participants)
        if not self._participants:
            await self.leave_call()

    # Mute control

    def set_muted(self, muted: bool) -> None:
        """
        Mute/unmute microphone.

        Args:
            muted: True to mute, False to unmute
        """
        if self._mic_track:
            self._mic_track.muted = muted

    @property
    def is_muted(self) -> bool:
        """Check if microphone is muted."""
        return self._mic_track.muted if self._mic_track else True

    # Cleanup

    async def _cleanup(self) -> None:
        """Clean up all resources."""
        # Close all peer connections
        for peer_state in list(self._peers.values()):
            try:
                await peer_state.connection.close()
            except Exception:
                pass

        self._peers.clear()

        # Stop microphone
        if self._mic_track:
            await self._mic_track.stop()
            self._mic_track = None

        self._participants.clear()
        self._call_id = None
        self._set_state(GroupCallState.ENDED)

    async def cleanup(self) -> None:
        """Public cleanup method."""
        await self._cleanup()
