"""
Voice call data models and state machine.

Provides data structures for voice calls, voice messages,
and call signaling events.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional
import uuid
import time


class CallState(Enum):
    """
    Voice call lifecycle states.

    State transitions:
    - IDLE -> RINGING_OUTGOING (initiating call)
    - IDLE -> RINGING_INCOMING (receiving call)
    - RINGING_OUTGOING -> CONNECTING (call answered)
    - RINGING_OUTGOING -> ENDED (rejected/no answer/cancelled)
    - RINGING_INCOMING -> CONNECTING (we answered)
    - RINGING_INCOMING -> ENDED (rejected by us)
    - CONNECTING -> ACTIVE (WebRTC connected)
    - CONNECTING -> ENDED (connection failed)
    - ACTIVE -> RECONNECTING (network changed)
    - ACTIVE -> ENDED (hangup)
    - RECONNECTING -> ACTIVE (reconnect succeeded)
    - RECONNECTING -> ENDED (reconnect failed)
    """
    IDLE = "idle"
    RINGING_OUTGOING = "ringing_outgoing"
    RINGING_INCOMING = "ringing_incoming"
    CONNECTING = "connecting"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    ENDED = "ended"


class CallEndReason(Enum):
    """
    Reasons why a voice call ended.
    """
    COMPLETED = "completed"  # Normal hangup by either party
    REJECTED = "rejected"  # Recipient rejected the call
    NO_ANSWER = "no_answer"  # Timeout waiting for answer (30 second default)
    FAILED = "failed"  # Connection failed (ICE/network error)
    CANCELLED = "cancelled"  # Caller cancelled before answer


@dataclass
class VoiceCall:
    """
    Represents an active or historical voice call.

    Tracks the complete lifecycle of a call from initiation
    through connection to termination.
    """
    call_id: str
    contact_id: int  # Database contact ID
    contact_public_key: str
    direction: Literal['outgoing', 'incoming']
    state: CallState = CallState.IDLE
    started_at: Optional[float] = None  # Timestamp when call started
    connected_at: Optional[float] = None  # Timestamp when ACTIVE state reached
    ended_at: Optional[float] = None  # Timestamp when call ended
    end_reason: Optional[CallEndReason] = None
    muted: bool = False  # Local mute state
    remote_muted: bool = False  # Peer's mute state
    # Video state fields
    video_enabled: bool = False  # Local video is on/off
    video_source: Optional[str] = None  # "camera" or "screen"
    remote_video: bool = False  # Remote party has video
    camera_device_id: Optional[int] = None  # Selected camera index

    @classmethod
    def create_outgoing(cls, contact_id: int, contact_public_key: str) -> 'VoiceCall':
        """Create a new outgoing call."""
        return cls(
            call_id=str(uuid.uuid4()),
            contact_id=contact_id,
            contact_public_key=contact_public_key,
            direction='outgoing',
            state=CallState.RINGING_OUTGOING,
            started_at=time.time()
        )

    @classmethod
    def create_incoming(cls, call_id: str, contact_id: int, contact_public_key: str) -> 'VoiceCall':
        """Create a new incoming call."""
        return cls(
            call_id=call_id,
            contact_id=contact_id,
            contact_public_key=contact_public_key,
            direction='incoming',
            state=CallState.RINGING_INCOMING,
            started_at=time.time()
        )

    def transition_to(self, new_state: CallState, end_reason: Optional[CallEndReason] = None) -> None:
        """
        Transition the call to a new state.

        Args:
            new_state: The target state.
            end_reason: Required when transitioning to ENDED state.
        """
        if new_state == CallState.ACTIVE and self.connected_at is None:
            self.connected_at = time.time()
        elif new_state == CallState.ENDED:
            self.ended_at = time.time()
            self.end_reason = end_reason

        self.state = new_state

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get call duration in seconds (only if call was connected)."""
        if self.connected_at is None:
            return None
        end_time = self.ended_at if self.ended_at else time.time()
        return end_time - self.connected_at


@dataclass
class VoiceMessageMetadata:
    """
    Metadata for a recorded voice message.

    Voice messages are stored as Opus-encoded .ogg files.
    Effect metadata can be stored to enable consistent playback across devices.
    """
    id: str
    duration_seconds: float
    sample_rate: int = 48000  # Opus standard
    file_path: Optional[str] = None  # Path to .ogg file
    created_at: float = field(default_factory=time.time)
    effects: Optional[dict] = None  # Serialized VoiceMessageEffectMetadata

    @classmethod
    def create(cls, duration_seconds: float, file_path: Optional[str] = None,
               effects: Optional[dict] = None) -> 'VoiceMessageMetadata':
        """
        Create a new voice message metadata entry.

        Args:
            duration_seconds: Duration of the voice message in seconds
            file_path: Path to the .ogg file
            effects: Effect metadata dictionary (from VoiceMessageEffectMetadata.to_dict())

        Returns:
            VoiceMessageMetadata instance
        """
        return cls(
            id=str(uuid.uuid4()),
            duration_seconds=duration_seconds,
            file_path=file_path,
            effects=effects
        )


@dataclass
class CallEvent:
    """
    Signaling event for voice calls.

    Used to coordinate call setup and teardown between peers
    via the signaling server.
    """
    type: Literal['call_offer', 'call_answer', 'call_reject', 'call_end', 'call_mute', 'call_video_renegotiate']
    call_id: str
    from_key: str  # Sender's public key
    to_key: str  # Recipient's public key
    sdp: Optional[str] = None  # For offer/answer events
    reason: Optional[CallEndReason] = None  # For end events
    muted: Optional[bool] = None  # For mute events
    # Video renegotiation fields
    video_enabled: Optional[bool] = None  # For video renegotiation events
    video_source: Optional[str] = None  # "camera" or "screen"

    @classmethod
    def create_offer(cls, call_id: str, from_key: str, to_key: str, sdp: str) -> 'CallEvent':
        """Create a call offer event."""
        return cls(
            type='call_offer',
            call_id=call_id,
            from_key=from_key,
            to_key=to_key,
            sdp=sdp
        )

    @classmethod
    def create_answer(cls, call_id: str, from_key: str, to_key: str, sdp: str) -> 'CallEvent':
        """Create a call answer event."""
        return cls(
            type='call_answer',
            call_id=call_id,
            from_key=from_key,
            to_key=to_key,
            sdp=sdp
        )

    @classmethod
    def create_reject(cls, call_id: str, from_key: str, to_key: str) -> 'CallEvent':
        """Create a call reject event."""
        return cls(
            type='call_reject',
            call_id=call_id,
            from_key=from_key,
            to_key=to_key,
            reason=CallEndReason.REJECTED
        )

    @classmethod
    def create_end(cls, call_id: str, from_key: str, to_key: str, reason: CallEndReason) -> 'CallEvent':
        """Create a call end event."""
        return cls(
            type='call_end',
            call_id=call_id,
            from_key=from_key,
            to_key=to_key,
            reason=reason
        )

    @classmethod
    def create_mute(cls, call_id: str, from_key: str, to_key: str, muted: bool) -> 'CallEvent':
        """Create a mute status event."""
        return cls(
            type='call_mute',
            call_id=call_id,
            from_key=from_key,
            to_key=to_key,
            muted=muted
        )

    @classmethod
    def create_video_renegotiate(
        cls,
        call_id: str,
        from_key: str,
        to_key: str,
        sdp: str,
        video_enabled: bool,
        video_source: Optional[str]
    ) -> 'CallEvent':
        """
        Create a video renegotiation event.

        Used when video track is added/removed/switched during a call.

        Args:
            call_id: Current call ID.
            from_key: Sender's public key.
            to_key: Recipient's public key.
            sdp: New SDP offer for renegotiation.
            video_enabled: Whether video is enabled after renegotiation.
            video_source: Video source type ("camera" or "screen"), None if video disabled.

        Returns:
            CallEvent for video renegotiation.
        """
        return cls(
            type='call_video_renegotiate',
            call_id=call_id,
            from_key=from_key,
            to_key=to_key,
            sdp=sdp,
            video_enabled=video_enabled,
            video_source=video_source
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            'type': self.type,
            'call_id': self.call_id,
            'from_key': self.from_key,
            'to_key': self.to_key
        }
        if self.sdp is not None:
            result['sdp'] = self.sdp
        if self.reason is not None:
            result['reason'] = self.reason.value
        if self.muted is not None:
            result['muted'] = self.muted
        if self.video_enabled is not None:
            result['video_enabled'] = self.video_enabled
        if self.video_source is not None:
            result['video_source'] = self.video_source
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'CallEvent':
        """Create from dictionary."""
        reason = None
        if data.get('reason'):
            reason = CallEndReason(data['reason'])

        return cls(
            type=data['type'],
            call_id=data['call_id'],
            from_key=data['from_key'],
            to_key=data['to_key'],
            sdp=data.get('sdp'),
            reason=reason,
            muted=data.get('muted'),
            video_enabled=data.get('video_enabled'),
            video_source=data.get('video_source')
        )
