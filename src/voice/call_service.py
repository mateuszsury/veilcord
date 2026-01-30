"""
Voice call service for managing call lifecycle.

Provides VoiceCallService class that orchestrates voice calls,
handling signaling, WebRTC peer connections, and audio tracks.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional

from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription, RTCIceServer

from src.voice.models import CallState, CallEndReason, VoiceCall, CallEvent
from src.voice.audio_track import MicrophoneAudioTrack, AudioPlaybackTrack
from src.network.stun import get_ice_servers


logger = logging.getLogger(__name__)


class VoiceCallService:
    """
    Manages voice call lifecycle with WebRTC.

    Handles call initiation, incoming call handling, state machine
    transitions, audio track management, and signaling coordination.

    Uses a separate RTCPeerConnection for voice calls (not the data
    channel connection) to allow media renegotiation.

    Attributes:
        on_state_change: Callback for call state changes.
        on_call_event: Callback for call events.
        send_signaling: Callback to send signaling messages.
    """

    def __init__(self):
        """Initialize the voice call service."""
        # Current call state
        self._current_call: Optional[VoiceCall] = None
        self._pc: Optional[RTCPeerConnection] = None  # Voice call peer connection
        self._mic_track: Optional[MicrophoneAudioTrack] = None
        self._playback: Optional[AudioPlaybackTrack] = None
        self._ice_complete = asyncio.Event()
        self._lock = asyncio.Lock()

        # Stored offer SDP for incoming calls (set when handling offer)
        self._pending_offer_sdp: Optional[str] = None

        # Callbacks (set by NetworkService)
        self.on_state_change: Optional[Callable[[int, CallState], None]] = None
        self.on_call_event: Optional[Callable[[CallEvent], None]] = None
        self.send_signaling: Optional[Callable[[dict], Any]] = None

        # Audio device settings
        self._input_device_id: Optional[int] = None
        self._output_device_id: Optional[int] = None

        # Timeouts
        self._ring_timeout = 30.0  # seconds
        self._ring_timeout_task: Optional[asyncio.Task] = None

        # Local identity (set by NetworkService)
        self._local_public_key: Optional[str] = None

        logger.info("VoiceCallService initialized")

    async def _create_peer_connection(self) -> RTCPeerConnection:
        """
        Create RTCPeerConnection configured for voice call.

        Returns:
            Configured RTCPeerConnection ready for audio tracks.
        """
        # Get ICE servers from existing stun module
        ice_servers_config = get_ice_servers()

        # Convert to RTCIceServer objects
        ice_servers = [
            RTCIceServer(urls=server["urls"])
            for server in ice_servers_config
        ]

        # Create configuration with ICE servers
        config = RTCConfiguration(iceServers=ice_servers)

        # Create peer connection
        pc = RTCPeerConnection(configuration=config)

        # Set up event handlers
        @pc.on("icegatheringstatechange")
        async def on_ice_gathering_state_change():
            logger.debug(f"ICE gathering state: {pc.iceGatheringState}")
            if pc.iceGatheringState == "complete":
                self._ice_complete.set()

        @pc.on("connectionstatechange")
        async def on_connection_state_change():
            logger.info(f"Connection state: {pc.connectionState}")
            if pc.connectionState == "failed":
                logger.error("Peer connection failed")
                await self.end_call(CallEndReason.FAILED)
            elif pc.connectionState == "disconnected":
                # Network change or temporary disconnect - don't immediately end
                logger.warning("Peer connection disconnected")
                if self._current_call and self._current_call.state == CallState.ACTIVE:
                    self._notify_state_change(
                        self._current_call.contact_id, CallState.RECONNECTING
                    )
            elif pc.connectionState == "connected":
                logger.info("Peer connection established")
                if self._current_call:
                    self._notify_state_change(
                        self._current_call.contact_id, CallState.ACTIVE
                    )

        @pc.on("track")
        async def on_track(track):
            logger.debug(f"Received track: {track.kind}")
            if track.kind == "audio":
                # Create playback for received audio
                self._playback = AudioPlaybackTrack(
                    device_id=self._output_device_id
                )
                # Start task to handle incoming audio
                asyncio.create_task(self._playback.handle_track(track))
                logger.info("Started audio playback for remote track")

        logger.debug("Created peer connection for voice call")
        return pc

    async def _wait_for_ice(self, timeout: float = 30.0) -> None:
        """
        Wait for ICE gathering to complete.

        Args:
            timeout: Maximum time to wait in seconds.

        Raises:
            asyncio.TimeoutError: If gathering doesn't complete in time.
        """
        self._ice_complete.clear()

        # Check if already complete
        if self._pc and self._pc.iceGatheringState == "complete":
            return

        await asyncio.wait_for(self._ice_complete.wait(), timeout)
        logger.debug("ICE gathering completed")

    async def start_call(
        self, contact_id: int, contact_public_key: str
    ) -> Optional[str]:
        """
        Start an outgoing voice call.

        Creates a WebRTC offer with audio track and sends it via signaling.

        Args:
            contact_id: Database ID of the contact to call.
            contact_public_key: Public key of the contact.

        Returns:
            Call ID on success, None if already in a call.
        """
        async with self._lock:
            # Check if already in a call
            if self._current_call and self._current_call.state != CallState.ENDED:
                logger.warning("Cannot start call: already in a call")
                return None

            # Generate call ID
            call_id = str(uuid.uuid4())
            logger.info(f"Starting outgoing call {call_id} to contact {contact_id}")

            # Create call object
            self._current_call = VoiceCall.create_outgoing(
                contact_id=contact_id,
                contact_public_key=contact_public_key
            )
            self._current_call.call_id = call_id

            try:
                # Create peer connection
                self._pc = await self._create_peer_connection()

                # Create and start microphone track
                self._mic_track = MicrophoneAudioTrack(
                    device_id=self._input_device_id
                )
                await self._mic_track.start()

                # Add mic track to peer connection
                self._pc.addTrack(self._mic_track)
                logger.debug("Added microphone track to peer connection")

                # Create offer
                offer = await self._pc.createOffer()
                await self._pc.setLocalDescription(offer)
                logger.debug("Created and set local offer")

                # Wait for ICE gathering to complete
                try:
                    await self._wait_for_ice(timeout=30.0)
                except asyncio.TimeoutError:
                    logger.error("ICE gathering timeout")
                    await self._cleanup()
                    self._current_call = None
                    return None

                # Get complete SDP with ICE candidates
                sdp = self._pc.localDescription.sdp

                # Create and send call offer event
                event = CallEvent.create_offer(
                    call_id=call_id,
                    from_key=self._local_public_key or "",
                    to_key=contact_public_key,
                    sdp=sdp
                )

                if self.send_signaling:
                    await self._send_signaling_async(event.to_dict())
                    logger.debug("Sent call offer via signaling")

                # Start ring timeout
                await self._start_ring_timeout()

                # Notify state change
                self._notify_state_change(contact_id, CallState.RINGING_OUTGOING)

                return call_id

            except Exception as e:
                logger.error(f"Failed to start call: {e}")
                await self._cleanup()
                self._current_call = None
                return None

    async def _send_signaling_async(self, message: dict) -> None:
        """
        Send signaling message, handling both sync and async callbacks.

        Args:
            message: Message dict to send.
        """
        if self.send_signaling:
            result = self.send_signaling(message)
            if asyncio.iscoroutine(result):
                await result

    async def handle_call_offer(self, event: CallEvent) -> bool:
        """
        Handle an incoming call offer.

        Stores the offer for later processing when user accepts.

        Args:
            event: Call offer event from signaling.

        Returns:
            True if call accepted for ringing, False if busy.
        """
        async with self._lock:
            # Check if already in a call
            if self._current_call and self._current_call.state != CallState.ENDED:
                logger.warning("Rejecting incoming call: already in a call")
                return False

            logger.info(f"Received incoming call {event.call_id}")

            # Look up contact ID from public key (NetworkService should provide this)
            # For now, use 0 as placeholder - NetworkService will set correct ID
            contact_id = 0

            # Create incoming call object
            self._current_call = VoiceCall.create_incoming(
                call_id=event.call_id,
                contact_id=contact_id,
                contact_public_key=event.from_key
            )

            # Store offer SDP for when user accepts
            self._pending_offer_sdp = event.sdp

            # Notify state change (triggers UI to show incoming call)
            self._notify_state_change(contact_id, CallState.RINGING_INCOMING)

            return True

    async def accept_call(self) -> bool:
        """
        Accept an incoming call.

        Called when user clicks accept button. Creates answer and
        establishes WebRTC connection.

        Returns:
            True on success, False if no incoming call to accept.
        """
        if not self._current_call or self._current_call.state != CallState.RINGING_INCOMING:
            logger.warning("No incoming call to accept")
            return False

        if not self._pending_offer_sdp:
            logger.error("No pending offer SDP")
            return False

        logger.info(f"Accepting call {self._current_call.call_id}")

        # Cancel ring timeout if running
        self._cancel_ring_timeout()

        # Transition to connecting
        self._notify_state_change(
            self._current_call.contact_id, CallState.CONNECTING
        )

        try:
            # Create peer connection
            self._pc = await self._create_peer_connection()

            # Set remote description from stored offer
            offer = RTCSessionDescription(
                sdp=self._pending_offer_sdp,
                type="offer"
            )
            await self._pc.setRemoteDescription(offer)
            logger.debug("Set remote offer description")

            # Create and start microphone track
            self._mic_track = MicrophoneAudioTrack(
                device_id=self._input_device_id
            )
            await self._mic_track.start()

            # Add mic track to peer connection
            self._pc.addTrack(self._mic_track)
            logger.debug("Added microphone track")

            # Create answer
            answer = await self._pc.createAnswer()
            await self._pc.setLocalDescription(answer)
            logger.debug("Created and set local answer")

            # Wait for ICE gathering
            try:
                await self._wait_for_ice(timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("ICE gathering timeout while accepting")
                await self._cleanup()
                return False

            # Send answer via signaling
            event = CallEvent.create_answer(
                call_id=self._current_call.call_id,
                from_key=self._local_public_key or "",
                to_key=self._current_call.contact_public_key,
                sdp=self._pc.localDescription.sdp
            )

            if self.send_signaling:
                await self._send_signaling_async(event.to_dict())
                logger.debug("Sent call answer via signaling")

            # Clear pending offer
            self._pending_offer_sdp = None

            return True

        except Exception as e:
            logger.error(f"Failed to accept call: {e}")
            await self._cleanup()
            return False

    async def reject_call(self) -> bool:
        """
        Reject an incoming call.

        Called when user clicks reject button.

        Returns:
            True on success, False if no incoming call to reject.
        """
        if not self._current_call or self._current_call.state != CallState.RINGING_INCOMING:
            logger.warning("No incoming call to reject")
            return False

        logger.info(f"Rejecting call {self._current_call.call_id}")

        # Send reject event
        event = CallEvent.create_reject(
            call_id=self._current_call.call_id,
            from_key=self._local_public_key or "",
            to_key=self._current_call.contact_public_key
        )

        if self.send_signaling:
            await self._send_signaling_async(event.to_dict())

        # End call locally
        await self.end_call(CallEndReason.REJECTED)

        return True

    async def handle_call_answer(self, event: CallEvent) -> None:
        """
        Handle an answer to our outgoing call.

        Sets remote description to complete WebRTC negotiation.

        Args:
            event: Call answer event from signaling.
        """
        if not self._current_call:
            logger.warning("No current call for answer")
            return

        if self._current_call.call_id != event.call_id:
            logger.warning(f"Call ID mismatch: {self._current_call.call_id} vs {event.call_id}")
            return

        if self._current_call.state != CallState.RINGING_OUTGOING:
            logger.warning(f"Wrong state for answer: {self._current_call.state}")
            return

        logger.info(f"Received answer for call {event.call_id}")

        # Cancel ring timeout
        self._cancel_ring_timeout()

        # Transition to connecting
        self._notify_state_change(
            self._current_call.contact_id, CallState.CONNECTING
        )

        try:
            # Set remote description
            answer = RTCSessionDescription(
                sdp=event.sdp,
                type="answer"
            )
            await self._pc.setRemoteDescription(answer)
            logger.debug("Set remote answer description")
            # Connection state handler will transition to ACTIVE when connected

        except Exception as e:
            logger.error(f"Failed to handle answer: {e}")
            await self.end_call(CallEndReason.FAILED)

    async def handle_call_reject(self, event: CallEvent) -> None:
        """
        Handle rejection of our outgoing call.

        Args:
            event: Call reject event from signaling.
        """
        if not self._current_call:
            return

        if self._current_call.call_id != event.call_id:
            return

        logger.info(f"Call {event.call_id} was rejected")
        await self.end_call(CallEndReason.REJECTED)

    async def handle_call_end(self, event: CallEvent) -> None:
        """
        Handle remote party ending the call.

        Args:
            event: Call end event from signaling.
        """
        if not self._current_call:
            return

        if self._current_call.call_id != event.call_id:
            return

        reason = event.reason or CallEndReason.COMPLETED
        logger.info(f"Remote party ended call {event.call_id}: {reason}")
        await self.end_call(reason)

    async def handle_call_mute(self, event: CallEvent) -> None:
        """
        Handle remote party mute status change.

        Args:
            event: Call mute event from signaling.
        """
        if not self._current_call:
            return

        if self._current_call.call_id != event.call_id:
            return

        self._current_call.remote_muted = event.muted or False
        logger.debug(f"Remote mute status: {self._current_call.remote_muted}")

    async def end_call(self, reason: CallEndReason = CallEndReason.COMPLETED) -> None:
        """
        End the current call.

        Cleans up resources and notifies remote party.

        Args:
            reason: Reason for ending the call.
        """
        if not self._current_call:
            return

        logger.info(f"Ending call {self._current_call.call_id}: {reason}")

        # Cancel ring timeout
        self._cancel_ring_timeout()

        # Send end event to remote (if not already ended by remote)
        if self._current_call.state != CallState.ENDED:
            event = CallEvent.create_end(
                call_id=self._current_call.call_id,
                from_key=self._local_public_key or "",
                to_key=self._current_call.contact_public_key,
                reason=reason
            )

            if self.send_signaling:
                try:
                    await self._send_signaling_async(event.to_dict())
                except Exception as e:
                    logger.debug(f"Failed to send end event: {e}")

        # Clean up resources
        await self._cleanup()

        # Update call state
        contact_id = self._current_call.contact_id
        self._current_call.transition_to(CallState.ENDED, reason)

        # Notify state change
        self._notify_state_change(contact_id, CallState.ENDED)

    async def _cleanup(self) -> None:
        """Clean up call resources."""
        if self._mic_track:
            try:
                await self._mic_track.stop()
            except Exception as e:
                logger.debug(f"Error stopping mic track: {e}")
            self._mic_track = None

        if self._playback:
            try:
                await self._playback.stop()
            except Exception as e:
                logger.debug(f"Error stopping playback: {e}")
            self._playback = None

        if self._pc:
            try:
                await self._pc.close()
            except Exception as e:
                logger.debug(f"Error closing peer connection: {e}")
            self._pc = None

        self._pending_offer_sdp = None
        self._ice_complete.clear()
        logger.debug("Call resources cleaned up")

    def set_muted(self, muted: bool) -> None:
        """
        Mute or unmute the local microphone.

        Sends mute status to remote party.

        Args:
            muted: True to mute, False to unmute.
        """
        if self._mic_track:
            self._mic_track.muted = muted

        if self._current_call:
            self._current_call.muted = muted

            # Send mute status to remote
            event = CallEvent.create_mute(
                call_id=self._current_call.call_id,
                from_key=self._local_public_key or "",
                to_key=self._current_call.contact_public_key,
                muted=muted
            )

            if self.send_signaling:
                # Fire and forget - mute status is not critical
                asyncio.create_task(self._send_signaling_async(event.to_dict()))

        logger.info(f"Local mute set to: {muted}")

    def is_muted(self) -> bool:
        """
        Check if locally muted.

        Returns:
            True if microphone is muted, False otherwise.
        """
        if self._current_call:
            return self._current_call.muted
        return False

    def _notify_state_change(self, contact_id: int, state: CallState) -> None:
        """
        Notify callback of state change.

        Updates internal call state and invokes callback.

        Args:
            contact_id: Contact ID for the call.
            state: New call state.
        """
        if self._current_call:
            if state == CallState.ACTIVE:
                self._current_call.transition_to(state)
            elif state == CallState.ENDED:
                # Already handled in end_call
                pass
            else:
                self._current_call.state = state

        if self.on_state_change:
            try:
                self.on_state_change(contact_id, state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")

        logger.info(f"Call state changed to {state.value}")

    def set_audio_devices(
        self, input_id: Optional[int], output_id: Optional[int]
    ) -> None:
        """
        Set audio devices to use for calls.

        Should be called before starting a call.

        Args:
            input_id: Input (microphone) device ID, or None for default.
            output_id: Output (speaker) device ID, or None for default.
        """
        self._input_device_id = input_id
        self._output_device_id = output_id
        logger.debug(f"Audio devices set: input={input_id}, output={output_id}")

    async def _start_ring_timeout(self) -> None:
        """Start timeout for unanswered call."""
        self._ring_timeout_task = asyncio.create_task(
            self._ring_timeout_handler()
        )

    async def _ring_timeout_handler(self) -> None:
        """Handle ring timeout."""
        try:
            await asyncio.sleep(self._ring_timeout)
            if self._current_call and self._current_call.state in (
                CallState.RINGING_OUTGOING, CallState.RINGING_INCOMING
            ):
                logger.info("Ring timeout - no answer")
                await self.end_call(CallEndReason.NO_ANSWER)
        except asyncio.CancelledError:
            pass  # Normal cancellation when call is answered

    def _cancel_ring_timeout(self) -> None:
        """Cancel ring timeout if call answered."""
        if self._ring_timeout_task and not self._ring_timeout_task.done():
            self._ring_timeout_task.cancel()
            self._ring_timeout_task = None

    async def attempt_reconnect(self) -> bool:
        """
        Attempt to reconnect a disconnected call.

        Per research: aiortc doesn't support ICE restart, so we must
        create a new peer connection and re-establish the call.

        Returns:
            True if reconnection initiated, False otherwise.
        """
        if not self._current_call:
            return False

        if self._current_call.state not in (
            CallState.RECONNECTING, CallState.ACTIVE
        ):
            logger.warning(f"Cannot reconnect from state: {self._current_call.state}")
            return False

        logger.info("Attempting to reconnect call")

        # Store contact info
        contact_id = self._current_call.contact_id
        contact_public_key = self._current_call.contact_public_key
        call_id = self._current_call.call_id

        # Notify state change
        self._notify_state_change(contact_id, CallState.RECONNECTING)

        # Clean up current connection (but don't end call)
        await self._cleanup()

        # Try to establish new connection
        try:
            # For reconnect, caller should re-initiate
            if self._current_call.direction == 'outgoing':
                # Create new connection as if starting call
                self._pc = await self._create_peer_connection()

                self._mic_track = MicrophoneAudioTrack(
                    device_id=self._input_device_id
                )
                await self._mic_track.start()

                self._pc.addTrack(self._mic_track)

                offer = await self._pc.createOffer()
                await self._pc.setLocalDescription(offer)

                await self._wait_for_ice(timeout=30.0)

                # Send reconnect offer (reuse call_id)
                event = CallEvent.create_offer(
                    call_id=call_id,
                    from_key=self._local_public_key or "",
                    to_key=contact_public_key,
                    sdp=self._pc.localDescription.sdp
                )

                if self.send_signaling:
                    await self._send_signaling_async(event.to_dict())

                return True
            else:
                # For incoming calls, wait for new offer from remote
                logger.info("Waiting for remote to reinitiate connection")
                return True

        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
            await self.end_call(CallEndReason.FAILED)
            return False

    def get_call_duration(self) -> Optional[float]:
        """
        Get current call duration in seconds.

        Returns:
            Duration in seconds if call is active, 0 if connecting,
            None if no call.
        """
        if not self._current_call:
            return None
        if self._current_call.connected_at is None:
            return 0.0
        return time.time() - self._current_call.connected_at

    @property
    def current_call(self) -> Optional[VoiceCall]:
        """Get the current call object."""
        return self._current_call

    def set_local_public_key(self, public_key: str) -> None:
        """
        Set the local public key for signaling.

        Called by NetworkService during initialization.

        Args:
            public_key: Local user's public key.
        """
        self._local_public_key = public_key
        logger.debug("Local public key set")
