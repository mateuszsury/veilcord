"""
Voice call service for managing call lifecycle.

Provides VoiceCallService class that orchestrates voice calls,
handling signaling, WebRTC peer connections, and audio/video tracks.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional, Union

import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription, RTCIceServer

from src.voice.models import CallState, CallEndReason, VoiceCall, CallEvent
from src.voice.audio_track import MicrophoneAudioTrack, AudioPlaybackTrack
from src.voice.video_track import CameraVideoTrack, ScreenShareTrack
from src.network.stun import get_ice_servers


logger = logging.getLogger(__name__)


class RemoteVideoHandler:
    """
    Handles incoming video track and stores frames.

    Processes video frames from remote peer and maintains
    the most recent frame for API access.
    """

    def __init__(self):
        """Initialize the remote video handler."""
        self._last_frame: Optional[np.ndarray] = None
        self._running = False

    async def handle_track(self, track) -> None:
        """
        Process incoming video track.

        Receives frames from the remote peer and stores them
        for retrieval via the last_frame property.

        Args:
            track: aiortc video track from remote peer.
        """
        self._running = True
        logger.info("Started remote video handler")

        try:
            while self._running:
                try:
                    frame = await asyncio.wait_for(track.recv(), timeout=1.0)
                    # Convert VideoFrame to numpy array
                    img = frame.to_ndarray(format='rgb24')
                    # Convert RGB to BGR for OpenCV (for JPEG encoding later)
                    self._last_frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                except asyncio.TimeoutError:
                    continue  # No frame available, keep waiting
                except Exception as e:
                    if self._running:
                        logger.debug(f"Remote video frame error: {e}")
                    break
        finally:
            logger.info("Remote video handler stopped")

    async def stop(self) -> None:
        """Stop handling remote video."""
        self._running = False

    @property
    def last_frame(self) -> Optional[np.ndarray]:
        """Get last received frame."""
        return self._last_frame


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

        # Video track management
        self._video_track: Optional[Union[CameraVideoTrack, ScreenShareTrack]] = None
        self._remote_video_handler: Optional[RemoteVideoHandler] = None
        self._camera_device_id: Optional[int] = None
        self._screen_monitor_index: int = 1

        # Callback for remote video state changes
        self.on_remote_video: Optional[Callable[[bool, Any], None]] = None

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
            elif track.kind == "video":
                # Create handler for remote video
                self._remote_video_handler = RemoteVideoHandler()
                # Start processing remote video frames
                asyncio.create_task(self._remote_video_handler.handle_track(track))
                logger.info("Started remote video handler for incoming track")

                # Update call state
                if self._current_call:
                    self._current_call.remote_video = True

                # Notify via callback
                if self.on_remote_video:
                    try:
                        self.on_remote_video(True, track)
                    except Exception as e:
                        logger.error(f"Error in remote video callback: {e}")

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

        # Clean up video track
        if self._video_track:
            try:
                await self._video_track.stop()
            except Exception as e:
                logger.debug(f"Error stopping video track: {e}")
            self._video_track = None

        # Clean up remote video handler
        if self._remote_video_handler:
            try:
                await self._remote_video_handler.stop()
            except Exception as e:
                logger.debug(f"Error stopping remote video handler: {e}")
            self._remote_video_handler = None

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

    # Video track management methods

    async def enable_video(self, video_source: str = "camera") -> bool:
        """
        Enable video during an active call.

        Creates a video track (camera or screen share) and adds it to the
        peer connection, triggering SDP renegotiation.

        Args:
            video_source: Type of video source - "camera" or "screen".

        Returns:
            True on success, False if call not active or error.
        """
        if not self._current_call:
            logger.warning("Cannot enable video: no active call")
            return False

        if self._current_call.state not in (CallState.ACTIVE, CallState.CONNECTING):
            logger.warning(f"Cannot enable video in state: {self._current_call.state}")
            return False

        if not self._pc:
            logger.warning("Cannot enable video: no peer connection")
            return False

        # If video already enabled with same source, no-op
        if (self._current_call.video_enabled and
                self._current_call.video_source == video_source):
            logger.debug(f"Video already enabled with source: {video_source}")
            return True

        # If video enabled with different source, disable first
        if self._current_call.video_enabled:
            logger.info(f"Switching video source from {self._current_call.video_source} to {video_source}")
            await self.disable_video()

        try:
            # Create appropriate video track
            if video_source == "camera":
                self._video_track = CameraVideoTrack(
                    device_id=self._camera_device_id or 0
                )
                logger.info(f"Created camera video track (device: {self._camera_device_id})")
            elif video_source == "screen":
                self._video_track = ScreenShareTrack(
                    monitor_index=self._screen_monitor_index
                )
                logger.info(f"Created screen share track (monitor: {self._screen_monitor_index})")
            else:
                logger.error(f"Unknown video source: {video_source}")
                return False

            # Add track to peer connection
            self._pc.addTrack(self._video_track)
            logger.debug("Added video track to peer connection")

            # Trigger renegotiation
            offer = await self._pc.createOffer()
            await self._pc.setLocalDescription(offer)

            # Wait for ICE gathering
            try:
                await self._wait_for_ice(timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("ICE gathering timeout during video enable")
                await self._video_track.stop()
                self._video_track = None
                return False

            # Send renegotiation event via signaling
            event = CallEvent.create_video_renegotiate(
                call_id=self._current_call.call_id,
                from_key=self._local_public_key or "",
                to_key=self._current_call.contact_public_key,
                sdp=self._pc.localDescription.sdp,
                video_enabled=True,
                video_source=video_source
            )

            if self.send_signaling:
                await self._send_signaling_async(event.to_dict())
                logger.debug("Sent video renegotiation offer")

            # Update call state
            self._current_call.video_enabled = True
            self._current_call.video_source = video_source

            logger.info(f"Video enabled: {video_source}")
            return True

        except Exception as e:
            logger.error(f"Failed to enable video: {e}")
            if self._video_track:
                try:
                    await self._video_track.stop()
                except Exception:
                    pass
                self._video_track = None
            return False

    async def disable_video(self) -> bool:
        """
        Disable video during an active call.

        Stops the video track and triggers SDP renegotiation.

        Returns:
            True on success, False if video not enabled or error.
        """
        if not self._current_call or not self._current_call.video_enabled:
            logger.debug("Video not enabled, nothing to disable")
            return True

        if not self._pc:
            logger.warning("Cannot disable video: no peer connection")
            return False

        try:
            # Stop current video track
            if self._video_track:
                await self._video_track.stop()
                self._video_track = None
                logger.debug("Stopped video track")

            # Trigger renegotiation
            # Note: aiortc doesn't support removeTrack, but stopping the track
            # should be sufficient. We create a new offer to update the SDP.
            offer = await self._pc.createOffer()
            await self._pc.setLocalDescription(offer)

            # Wait for ICE gathering
            try:
                await self._wait_for_ice(timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("ICE gathering timeout during video disable")
                # Continue anyway - video is already stopped locally

            # Send renegotiation event via signaling
            event = CallEvent.create_video_renegotiate(
                call_id=self._current_call.call_id,
                from_key=self._local_public_key or "",
                to_key=self._current_call.contact_public_key,
                sdp=self._pc.localDescription.sdp,
                video_enabled=False,
                video_source=None
            )

            if self.send_signaling:
                await self._send_signaling_async(event.to_dict())
                logger.debug("Sent video disable renegotiation")

            # Update call state
            self._current_call.video_enabled = False
            self._current_call.video_source = None

            logger.info("Video disabled")
            return True

        except Exception as e:
            logger.error(f"Failed to disable video: {e}")
            return False

    def set_camera_device(self, device_id: int) -> None:
        """
        Set the camera device to use for video calls.

        Should be called before enabling video.

        Args:
            device_id: Camera device ID from device enumeration.
        """
        self._camera_device_id = device_id
        logger.debug(f"Camera device set: {device_id}")

    def set_screen_monitor(self, monitor_index: int) -> None:
        """
        Set the monitor to use for screen sharing.

        Should be called before enabling screen share.

        Args:
            monitor_index: Monitor index (1=primary, 2+=additional).
        """
        self._screen_monitor_index = monitor_index
        logger.debug(f"Screen monitor set: {monitor_index}")

    def get_local_video_frame(self) -> Optional[np.ndarray]:
        """
        Get the last captured local video frame.

        Returns:
            BGR numpy array of the last frame, or None if no video active.
        """
        if self._video_track and hasattr(self._video_track, 'last_frame'):
            frame = self._video_track.last_frame
            if frame is not None:
                # Convert from RGB (video track format) to BGR (for JPEG encoding)
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return None

    def get_remote_video_frame(self) -> Optional[np.ndarray]:
        """
        Get the last received remote video frame.

        Returns:
            BGR numpy array of the last frame, or None if no remote video.
        """
        if self._remote_video_handler:
            return self._remote_video_handler.last_frame
        return None

    async def handle_video_renegotiate(self, event: CallEvent) -> None:
        """
        Handle a video renegotiation event from remote peer.

        Called when remote peer enables/disables/switches video.

        Args:
            event: Video renegotiation event from signaling.
        """
        if not self._current_call:
            logger.warning("No current call for video renegotiate")
            return

        if self._current_call.call_id != event.call_id:
            logger.warning(f"Call ID mismatch: {self._current_call.call_id} vs {event.call_id}")
            return

        if not self._pc:
            logger.warning("No peer connection for video renegotiate")
            return

        logger.info(f"Handling video renegotiation: video_enabled={event.video_enabled}, source={event.video_source}")

        try:
            # Set remote description from the offer
            offer = RTCSessionDescription(
                sdp=event.sdp,
                type="offer"
            )
            await self._pc.setRemoteDescription(offer)
            logger.debug("Set remote video renegotiation offer")

            # Create and send answer
            answer = await self._pc.createAnswer()
            await self._pc.setLocalDescription(answer)

            # Wait for ICE gathering
            try:
                await self._wait_for_ice(timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("ICE gathering timeout during video renegotiate answer")
                return

            # Send answer back via signaling
            # Use the same event type but with our SDP as the answer
            answer_event = CallEvent(
                type='call_video_renegotiate',
                call_id=self._current_call.call_id,
                from_key=self._local_public_key or "",
                to_key=self._current_call.contact_public_key,
                sdp=self._pc.localDescription.sdp,
                video_enabled=event.video_enabled,
                video_source=event.video_source
            )

            if self.send_signaling:
                await self._send_signaling_async(answer_event.to_dict())
                logger.debug("Sent video renegotiation answer")

            # Log video state change
            if event.video_enabled:
                logger.info(f"Remote enabled video: {event.video_source}")
            else:
                logger.info("Remote disabled video")
                # Clear remote video state
                if self._current_call:
                    self._current_call.remote_video = False
                # Notify via callback
                if self.on_remote_video:
                    try:
                        self.on_remote_video(False, None)
                    except Exception as e:
                        logger.error(f"Error in remote video callback: {e}")

        except Exception as e:
            logger.error(f"Failed to handle video renegotiate: {e}")

    async def handle_video_renegotiate_offer(self, event: CallEvent) -> bool:
        """
        Handle a video renegotiation offer from remote peer.

        Remote party is adding/changing/removing video.

        Args:
            event: CallEvent with video renegotiation offer

        Returns:
            True on success, False on failure
        """
        if not self._current_call or not self._pc:
            logger.warning("Cannot handle video offer: no call/connection")
            return False

        logger.info(f"Handling video renegotiation offer: video_enabled={event.video_enabled}")

        try:
            # Set remote description from the offer
            offer = RTCSessionDescription(
                sdp=event.sdp,
                type="offer"
            )
            await self._pc.setRemoteDescription(offer)
            logger.debug("Set remote video renegotiation offer")

            # Create and send answer
            answer = await self._pc.createAnswer()
            await self._pc.setLocalDescription(answer)

            # Wait for ICE gathering
            try:
                await self._wait_for_ice(timeout=30.0)
            except asyncio.TimeoutError:
                logger.error("ICE gathering timeout during video renegotiate answer")
                return False

            # Send answer back via signaling
            answer_msg = {
                'type': 'call_video_renegotiate',
                'call_id': self._current_call.call_id,
                'from': self._local_public_key or "",
                'to': self._current_call.contact_public_key,
                'sdp': self._pc.localDescription.sdp,
                'sdp_type': 'answer',
                'video_enabled': event.video_enabled,
                'video_source': event.video_source
            }

            if self.send_signaling:
                await self._send_signaling_async(answer_msg)
                logger.debug("Sent video renegotiation answer")

            # Update remote video state
            self._current_call.remote_video = event.video_enabled or False

            # Notify via callback
            if self.on_remote_video:
                try:
                    self.on_remote_video(event.video_enabled or False, None)
                except Exception as e:
                    logger.error(f"Error in remote video callback: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to handle video renegotiation offer: {e}")
            return False

    async def handle_video_renegotiate_answer(self, event: CallEvent) -> bool:
        """
        Handle a video renegotiation answer from remote peer.

        Response to our video enable/disable request.

        Args:
            event: CallEvent with video renegotiation answer

        Returns:
            True on success, False on failure
        """
        if not self._current_call or not self._pc:
            logger.warning("Cannot handle video answer: no call/connection")
            return False

        logger.info("Handling video renegotiation answer")

        try:
            # Set remote description (the answer)
            answer = RTCSessionDescription(
                sdp=event.sdp,
                type="answer"
            )
            await self._pc.setRemoteDescription(answer)
            logger.debug("Set remote video renegotiation answer")

            return True

        except Exception as e:
            logger.error(f"Failed to handle video renegotiation answer: {e}")
            return False
